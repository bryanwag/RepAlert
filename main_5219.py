# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 10:16:58 2019

@author: bryan
"""

#as long as input is incorrect, flag will be 0 and while loop will keep going
flag=0
while flag==0:
    print("Would you like to run the initializer or the updater?")
    answer=input()
    if "initializer" in answer:
        print("Please enter your desired votes threshold:")
        num=input()
        if num.isdigit():
            flag=1
            votes_threshold=float(num)
            print(f"Setting vote threshold to {num} NANO.\n")
            import initialize_official_rep_delegator_status_5219 as init
            if __name__ == '__main__':
                print('Initializing status...\n')
                official_rep_list=init.get_official_rep_list()
                badrep_df=init.get_badrep_df()
                delegators_df=init.get_delegators(official_rep_list,votes_threshold)
                delegators_df.to_csv('official_delegators.csv')
                print('Creating a backup csv in case this script is mistakenly run.')
                delegators_df.to_csv('RENAME_ME_backup.csv')
                print("Please change the name of 'RENAME_ME_backup.csv' so it won't be overwritten!")
                delegators=delegators_df
                status=init.get_delegators_status_df(delegators_df,badrep_df,votes_threshold)
                print('Initializing completed. Check variable "status".\n')
        else:
            print("Incorrect input. Please enter a valid number.\n")
    elif "updater" in answer:
        print("Please enter your desired votes threshold:")
        num=input()
        if num.isdigit():
            flag=1
            votes_threshold=float(num)
            print(f"Setting vote threshold to {num} NANO.\n")
            import update_official_rep_delegator_status_5219 as update, pandas as pd
            if __name__ == '__main__':
                print('Updating status...\n')
                official_rep_list=update.get_official_rep_list()
                badrep_df=update.get_badrep_df()
                delegators=pd.read_csv('official_delegators.csv',index_col=0)
                status=update.get_delegators_status_df(delegators,badrep_df,votes_threshold)
                print('Updating completed. Check variable "status".\n')
        else:
            print("Incorrect input. Please enter a valid number.\n")
    else:
        print("Incorrect input. Please type either 'initializer' or 'updater'.\n")
