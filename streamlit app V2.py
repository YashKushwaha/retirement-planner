# -*- coding: utf-8 -*-
"""
Created on Sun Nov  6 20:30:45 2022

@author: Yash
"""

import streamlit as st
import os

def show_options(x):
    if x == 'a':
        out = 'I want to know how much to save every year for my retirement portfolio'
    elif x == 'b':
        out = 'I want to know how many years my retirement portfolio will last'
    elif x == 'c':
        out = 'Let me figure out my retirement planning'
    else:
        out = ''
        
    return out

def func():
    SIP_AMOUNT_YEARLY = st.number_input('ABC?',value=10000, step=100, format = '%d',key='a' )        
    SIP_AMOUNT_YEARLY_INCREMENT = st.number_input('XYZ', step=0.01, key='b' )
    return SIP_AMOUNT_YEARLY, SIP_AMOUNT_YEARLY_INCREMENT

def sidebar():
    with st.sidebar:
        st.subheader('ASSUMPTIONS USED')
        RATE_OF_RETURN_PRE_RETIREMENT = st.number_input('Expencted return on portfolio pre retirement',
                                                    min_value =0.0, max_value=1.0, step=0.01, value=0.05 )
        SIP_AMOUNT_YEARLY_INCREMENT = st.number_input('Increase in contribution pre retirement every year', step=0.01 )
        RATE_OF_INFLATION_POST_RETIREMENT = st.number_input('Lifestype inflation expectd post retirement', step=0.01 )
        RATE_OF_RETURN_POST_RETIREMENT = st.number_input('Expencted return on portfolio pre retirement', step=0.01, value=0.05 )
    
    return (RATE_OF_RETURN_PRE_RETIREMENT, SIP_AMOUNT_YEARLY_INCREMENT,
        RATE_OF_INFLATION_POST_RETIREMENT,RATE_OF_RETURN_POST_RETIREMENT)

def find_annual_contribution_requirement():
    num_years = RETIREMENT_AGE - CURRENT_AGE
    
    if num_years > 0:
        message = f'Great! You have {RETIREMENT_AGE - CURRENT_AGE} years to build your retirement portfolio'
    else:
        message = f'Please select an retirement age that is greater than current age'
    
    st.write(message) 
    
    st.markdown("""<hr style="height:1px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)              
       
    col1, col2 = st.columns([3,2])
    
    portfolio_goal_input_label = 'What is your target for retirement corpus?'
    col1.write(portfolio_goal_input_label)
    portfolio_goal = col2.number_input(portfolio_goal_input_label,
                                  label_visibility = 'collapsed', key = 'portfolio_goal',
                                  value=10000, step=100, format = '%d' )
    
    col3, col4 = st.columns([3,2])
    
    current_portfolio_input_label = 'What is your current portfolio size?'    
    col3.write(current_portfolio_input_label)
    
    current_portfolio_size = col4.number_input(current_portfolio_input_label,
                                  label_visibility = 'collapsed', key = 'current_portfolio_size',
                                  value=0, step=100, format = '%d' )
    
    
    fv_current_portfolio_size = future_value(current_portfolio_size,
            rate_of_return = RATE_OF_RETURN_PRE_RETIREMENT, num_years=num_years)
    
    portfolio_shortfall = int(portfolio_goal - fv_current_portfolio_size)
    
    if portfolio_shortfall > 0:    
        yearly_contribution = calculate_emi(portfolio_shortfall, RATE_OF_RETURN_PRE_RETIREMENT, num_years, remaining_balance=0)    
        text = f'You need to contribute USD {int(yearly_contribution)} annually to get a retirement corpus of USD {portfolio_goal} in {num_years} years '
    else:
        yearly_contribution = 0
        text = f"""You don't need to make any contributions. Your current portfolio of USD {current_portfolio_size} will become USD {int(fv_current_portfolio_size)} in {num_years} years"""
    
    st.write(text)
   
    future_value_of_SIP = get_future_value_of_SIP_at_any_point(
            sip_amount = yearly_contribution, rate_of_return = RATE_OF_RETURN_PRE_RETIREMENT,
            num_years = num_years, rate_of_SIP_increase=SIP_AMOUNT_YEARLY_INCREMENT,
            current_balance=current_portfolio_size)
        
    future_value_of_SIP_df = pd.DataFrame(future_value_of_SIP)
    future_value_of_SIP_df = future_value_of_SIP_df.applymap(lambda x: int(round(x,0)))
    future_value_of_SIP_df['Age'] = future_value_of_SIP_df['t'].apply(lambda x: int(x) + CURRENT_AGE)
    
    display_options = st.radio(
        "Select one of the options to see how your portfolio evolves with time: ",
        ( 'Plot', 'Table'), index=0, key='sip', horizontal = True)
    
    
    with st.container():
        if display_options == 'Table':
            future_value_of_SIP_df_to_print = future_value_of_SIP_df.set_index('t')
            st.write(future_value_of_SIP_df_to_print)
        else:
            fig = plot_portfolio(future_value_of_SIP_df, 'Age')
            st.plotly_chart(fig)    
    
    st.markdown("""<hr style="height12px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
    
    
    portfolio_value_at_retirement = future_value_of_SIP_df['total_portfolio_value'].tolist()[-1]
    statement  = f'Your retirement portfolio size will be $ {portfolio_value_at_retirement}'
    st.write(statement)
    
    return None

def find_retirement_portfolio_life():
    RETIREMENT_PORTFOLIO = st.number_input('How much money you expect to have at your retirement?', step=1000, value=1000000)
    
    SWP_AMOUNT_YEARLY = st.number_input('How much money you want to withdraw every year?', step=100, value=90000 )
      
    max_years, tracker = find_how_many_years_the_account_will_last(
        sip_amount = SWP_AMOUNT_YEARLY, rate_of_return = RATE_OF_RETURN_POST_RETIREMENT,
        rate_of_SIP_increase=RATE_OF_INFLATION_POST_RETIREMENT,
        current_balance=RETIREMENT_PORTFOLIO)    
    
    tracker_df = pd.DataFrame(tracker).applymap(lambda x: int(round(x,0)))
    tracker_df['Age'] = tracker_df['t'].apply(lambda x: int(x) + RETIREMENT_AGE)
    
    statement  = f'Your retirement portfolio will last for ==> {max_years} years'
    st.write(statement)
    
    display_options_retirement = st.radio(
        "Select one of the options to see detailed analysis: ",
        ( 'Plot', 'Table',), index=0, key='swp', horizontal = True)
    
    with st.container():
        if display_options_retirement == 'Table':
            st.write(tracker_df)
        else:
            fig = plot_swp_portfolio(tracker_df, 'Age')
            st.plotly_chart(fig)

    return None    

    
if __name__ == '__main__':
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    except:
        cwd = r'C:\Users\Yash\Desktop\Codes'
        os.chdir(cwd)
    
    from retirement_planner import *

    st.title('RETIREMENT PLANNER')
    st.subheader('How may I help you with you retirement planning?')
    
    display_options = st.radio(
        "TEMP",
        ( 'a', 'b','c'),  key='options', index=0,
        format_func = show_options,
        label_visibility = 'collapsed')    
    
    CURRENT_AGE = st.slider('What is your current age?', 18, 70, 50) 
    #RETIREMENT_AGE = st.slider('At what age you want to retire?', min(CURRENT_AGE, 70, CURRENT_AGE-1), 70, 65)
    RETIREMENT_AGE = st.slider('At what age you want to retire?', 18, 70, 65)    
    
    RATE_OF_RETURN_PRE_RETIREMENT, SIP_AMOUNT_YEARLY_INCREMENT, RATE_OF_INFLATION_POST_RETIREMENT,RATE_OF_RETURN_POST_RETIREMENT = sidebar()
    
    if display_options == 'a':
        find_annual_contribution_requirement()
    elif display_options == 'b':
        find_retirement_portfolio_life()
    elif display_options == 'c':
        find_annual_contribution_requirement()
        find_retirement_portfolio_life()
    else:
        pass
        

