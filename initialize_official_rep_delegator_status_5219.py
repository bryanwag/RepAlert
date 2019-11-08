# -*- coding: utf-8 -*-
"""
Created on Sun Feb  3 12:38:21 2019

@author: bryan
"""
import pandas as pd,math,numpy as np,json,requests,random

#set votes threshold (in NANO) to filter delegators
#votes_threshold=10000
###############################################################################

def get_official_rep_list():
    url='https://nanocharts.info/data/representatives-by-category.json'
    response=requests.get(url)
    data = json.loads(response.text)
    official_rep=[]
    for i in range(len(data['categories']['official'])):
        official_rep.append(data['categories']['official'][i]['address'])
    #official_rep_df = pd.DataFrame(index=np.array(official_rep))
    return official_rep

def get_badrep_df():
    url='https://nanocharts.info/data/representatives-by-category.json'
    response=requests.get(url)
    data = json.loads(response.text)
    badrep=[]
    for i in range(len(data['categories']['offline'])):
        badrep.append(data['categories']['offline'][i]['address'])
    
    badrep_df = pd.DataFrame(index=np.array(badrep))
    #csv_final=df_final.to_csv
    return badrep_df

def get_delegators(replist,votes_threshold):
    df=pd.DataFrame(columns=['RepAddy','VotingWeights'])
    for addy in replist:
        addy=str(addy)
        url='https://api.nanocrawler.cc/v2/accounts/'+addy+'/delegators'
        try:
            df2=pd.read_json(url)
        except:
            print("Error: "+url)
            continue
        else:
            df2.insert(0,'RepAddy',addy)
            df2.columns=['RepAddy','VotingWeights']
            df=df.append(df2)

    df['VotingWeights']*=1/10**30
    delegators_df = df[(df['VotingWeights'] > votes_threshold)]
    return delegators_df

def get_delegators_status_df(delegators,badrep,votes_threshold):
    #initialize dataframe
    delegators.insert(2,'redelegatability',-1)
    delegators.insert(3,'next_spam_number',-1)
    delegators.insert(4,'success',-1)
    delegators.insert(5,'new_rep',-1)
    #there will be corner cases that my code can't cover. If my code detects any anomaly, at least it will be flagged for manual checking.
    delegators.insert(6,'worth_checking',-1)
    #if they moved their fund away, I flag the receiver address with max send amount as a potential alt account
    delegators.insert(7,'potential_alt_account','')
    
    #vanity accounts
    cr_account='xrb_1chngrepnja6patkegbrqjitjtg5h7tyeri5ea1g6f7rzoiees5pu8y6z9ya'
    br_account='xrb_3badrep9q8w14ngrwhz7ps4awn1aqxcthch7ohthxa5jse5p4s48ieb1xe6e'  
    cg_account='xrb_1changem17un1kmh8k5kswt6gnseo7fj8ff8euckbf3sixe49m6sbipgbe8a'
    #cutoff threshold for balance
    threshold=votes_threshold*10**30
    
    counter=1
    tot=str(len(delegators.index))
    #loop through delegator addresses
    for addy in delegators.index:
        #print progress
        print(str(counter) + " out of " + tot + " delegators")
        counter+=1
        
        #get the total transaction number of the account
        url='https://api.nanocrawler.cc/v2/accounts/'+addy+'/'
        try:
            df1=pd.read_json(url,dtype=False)
        except:
            delegators.loc[addy,'redelegatability']=-99
            continue #go to next account
        else:
            transaction_number=int(df1.loc['block_count','account'])
            current_rep=df1.loc['representative','account']
            old_rep=delegators.loc[addy,'RepAddy']
            if current_rep==old_rep:
                delegators.loc[addy,'success']=0
            elif current_rep not in badrep.index:
                delegators.loc[addy,'success']=1 #if rep is changed to a non-official or non-badrep, success
                delegators.loc[addy,'new_rep']=current_rep
            else:
                delegators.loc[addy,'success']=0
                
            #if there is no successful change, we need the rest of info to determine how to send txns
            if delegators.loc[addy,'success']==0:
                #we need to increase txns for high transaction number accounts
                if transaction_number<100:
                    #the floor value is 2
                    delegators.loc[addy,'next_spam_number']=2
                else:
                    #higher transaction number
                    delegators.loc[addy,'next_spam_number']=random.randint(2,5)
                    
                #we check whether the account has pending txns from our addresses
                url='https://api.nanocrawler.cc/v2/accounts/'+addy+'/pending'
                response=requests.get(url)
                try:
                    pending = json.loads(response.text)
                except:
                    delegators.loc[addy,'redelegatability']=-99
                    continue #go to next account
                else:
                    #cannot pass 50 pendings
                    if pending['total']>=50-delegators.loc[addy,'next_spam_number']:
                        delegators.loc[addy,'redelegatability']=0
                    else:
                        delegators.loc[addy,'redelegatability']=1
                        for i in range(len(pending['blocks'])):
                            #if pending exists, that means it's currently not redelegatable, it's not a virgin, and we shouldn't send more txns
                            if pending['blocks'][i]['source'] == cr_account or pending['blocks'][i]['source'] == br_account or pending['blocks'][i]['source'] == cg_account:
                                delegators.loc[addy,'redelegatability']=0
                                break
                #now go to account history
                url='https://api.nanocrawler.cc/v2/accounts/'+addy+'/history'
                try:
                    df2=pd.read_json(url)
                except:
                    delegators.loc[addy,'redelegatability']=-99
                    continue #go to next account
                else:
                    #if balance is no longer above threshold (corner case)
                    if float(df1.loc['balance','account'])<threshold:
                        #find the max send since spam
                        df3=df2[(df2['subtype'] == 'send')]
                        #we should no longer notify them
                        delegators.loc[addy,'redelegatability']=0
                        #empty means they sent the fund before receiving spam
                        if df3.empty:
                            pass
                        #if they move it to another account we already have on file (no need for further action)
                        elif df3['account'][df3['amount'].idxmax] in delegators.index:
                            delegators.loc[addy,'worth_checking']=1
                        else:
                            #if they move it to another account we don't have on file yet, flag it
                            delegators.loc[addy,'worth_checking']=1
                            delegators.loc[addy,'potential_alt_account']=df3['account'][df3['amount'].idxmax]

            if delegators.loc[addy,'success']==1:
                    delegators.loc[addy,'redelegatability']=-1
    return delegators


if __name__ == '__main__':
    votes_threshold=1000000
    print('Initializing status...\n')
    official_rep_list=get_official_rep_list()
    badrep_df=get_badrep_df()
    delegators_df=get_delegators(official_rep_list,votes_threshold)
    delegators_df.to_csv('official_delegators.csv')
    print('Creating a backup csv in case this script is mistakenly run.')
    delegators_df.to_csv('official_delegators_backup.csv')
    print("Please change the name of 'official_delegators_backup.csv' so it won't be overwritten!")
    delegators=delegators_df
    status=get_delegators_status_df(delegators_df,badrep_df,votes_threshold)
    print('Initializing completed. Check variable "status".\n')