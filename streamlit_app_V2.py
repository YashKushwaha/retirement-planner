# -*- coding: utf-8 -*-
"""
Created on Sun Nov  6 20:30:45 2022

@author: Yash
"""

import streamlit as st
import os

def sidebar():
    with st.sidebar:
        st.subheader('ASSUMPTIONS USED')
        RATE_OF_RETURN_PRE_RETIREMENT = st.number_input('Expected return on portfolio PRE retirement',
                                                    min_value =-0.0, max_value=1.0, step=0.01, value=0.05 )
        SIP_AMOUNT_YEARLY_INCREMENT = st.number_input('Increase in contribution PRE retirement every year', 
                step=0.01, min_value =-0.0 )
        RATE_OF_INFLATION_POST_RETIREMENT = st.number_input('Lifestyle inflation expectd POST retirement',
                step=0.01, min_value =-0.0 )
        RATE_OF_RETURN_POST_RETIREMENT = st.number_input('Expected return on portfolio POST retirement', 
                step=0.01, value=0.05, min_value =-0.0 )
    
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
                                  value=10000, step=100 )#, format = '%d'
    
    col3, col4 = st.columns([3,2])
    
    current_portfolio_input_label = 'What is your current portfolio size?'    
    col3.write(current_portfolio_input_label)
    
    current_portfolio_size = col4.number_input(current_portfolio_input_label,
                                  label_visibility = 'collapsed', key = 'current_portfolio_size',
                                  value=0, step=100, min_value = 0 ) #format = '%d',
    
    
    fv_current_portfolio_size = future_value(current_portfolio_size,
            rate_of_return = RATE_OF_RETURN_PRE_RETIREMENT, num_years=num_years)
    
    portfolio_shortfall = int(portfolio_goal - fv_current_portfolio_size)
    #st.write(portfolio_shortfall)
    if portfolio_shortfall > 0:    
        yearly_contribution = calculate_emi(portfolio_shortfall, RATE_OF_RETURN_PRE_RETIREMENT, num_years, remaining_balance=0)    
        text = f'You need to contribute USD {int(yearly_contribution):,} annually to get a retirement corpus of USD {portfolio_goal:,} in {num_years} years '
    else:
        yearly_contribution = 0
        text = f"""You don't need to make any contributions. Your current portfolio of USD {current_portfolio_size:,} will become USD {int(fv_current_portfolio_size):,} in {num_years} years"""
    
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
    
    #st.markdown("""<hr style="height12px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
    
    
    portfolio_value_at_retirement = future_value_of_SIP_df['total_portfolio_value'].tolist()[-1]
    statement  = f'Your retirement portfolio size will be $ {portfolio_value_at_retirement}'
    #st.markdown("""<hr style="height2px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
    #st.write(statement)
    
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
    
    statement  = f'Your retirement portfolio will last for {max_years} years'
    #st.markdown("""<hr style="height2px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
    st.write(statement)
    #st.markdown("""<hr style="height2px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
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

def get_inputs_for_sip_and_portfolio():
    col1, col2 = st.columns([3,2])
    SIP_AMOUNT_YEARLY_label = 'How much you want to save every year?'
    col1.write(SIP_AMOUNT_YEARLY_label)
    
    SIP_AMOUNT_YEARLY = col2.number_input(SIP_AMOUNT_YEARLY_label,
                                  label_visibility = 'collapsed', key = 'SIP_AMOUNT_YEARLY',
                                  value=10000, step=1000, format = '%d' )
    
    col3, col4 = st.columns([3,2])    
    current_portfolio_input_label = 'What is your current portfolio size?'    
    col3.write(current_portfolio_input_label)    
    current_portfolio_size = col4.number_input(current_portfolio_input_label,
                                  label_visibility = 'collapsed', key = 'current_portfolio_size',
                                  value=200000, step=1000, format = '%d' )
    
    col5, col6 = st.columns([3,2])    
    SWP_label = 'How much money you want to withdraw every year POST RETIREMENT?'    
    col5.write(SWP_label)    
    SWP = col6.number_input(SWP_label,
                                  label_visibility = 'collapsed', key = 'SWP_label',
                                  value=90000, step=1000, format = '%d' )

    return SIP_AMOUNT_YEARLY, current_portfolio_size, SWP

def show_options(x):
    if x == 'a':
        out = 'I want to know how much to save every year to achieve my retirement portfolio goals'
    elif x == 'b':
        out = 'I want to know how many years my retirement portfolio will last'
    elif x == 'c':
        out = 'I want to know how long my retirement corpus last based on my savings pre retirement'
    else:
        out = 'Let me figure out my retirement planning'
        
    return out
    
def find_retirement_corpus_life_based_on_annual_contribution():   
    num_years = RETIREMENT_AGE - CURRENT_AGE
    SIP_AMOUNT_YEARLY, current_portfolio_size, SWP = get_inputs_for_sip_and_portfolio()

    future_value_of_SIP = get_future_value_of_SIP_at_any_point(
            sip_amount = SIP_AMOUNT_YEARLY, rate_of_return = RATE_OF_RETURN_PRE_RETIREMENT,
            num_years = num_years, rate_of_SIP_increase=SIP_AMOUNT_YEARLY_INCREMENT,
            current_balance=current_portfolio_size)
        
    future_value_of_SIP_df = pd.DataFrame(future_value_of_SIP)
    future_value_of_SIP_df = future_value_of_SIP_df.applymap(lambda x: int(round(x,0)))
    future_value_of_SIP_df['Age'] = future_value_of_SIP_df['t'].apply(lambda x: int(x) + CURRENT_AGE)
    
    portfolio_value_at_retirement = future_value_of_SIP_df['total_portfolio_value'].tolist()[-1]
    statement  = f'Your retirement portfolio size will be $ {portfolio_value_at_retirement:,}'
    st.write(statement)    
    
    max_years, tracker = find_how_many_years_the_account_will_last(
        sip_amount = SWP, rate_of_return = RATE_OF_RETURN_POST_RETIREMENT,
        rate_of_SIP_increase=RATE_OF_INFLATION_POST_RETIREMENT,
        current_balance=portfolio_value_at_retirement)    

    tracker_df = pd.DataFrame(tracker).applymap(lambda x: int(round(x,0)))
    tracker_df['Age'] = tracker_df['t'].apply(lambda x: int(x) + RETIREMENT_AGE)
    tracker_df = tracker_df[tracker_df['period_end_balance']>0]
    
    statement  = f'Your retirement portfolio will last for {max_years} years'
    st.write(statement)        
    
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
    
    display_options_retirement = st.radio(
        "Select one of the options to see detailed analysis: ",
        ( 'Plot', 'Table',), index=0, key='swp', horizontal = True)
    
    with st.container():
        if display_options_retirement == 'Table':
            st.write(tracker_df)
        else:
            fig = plot_swp_portfolio(tracker_df, 'Age')
            st.plotly_chart(fig)
    
    st.markdown("""<hr style="height2px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)
    return None

def get_current_age_retirement_age_inputs():
    CURRENT_AGE_label, CURRENT_AGE_col = st.columns([3,4])  
    CURRENT_AGE_label_text = 'What is your current age?'
    CURRENT_AGE_label.write(CURRENT_AGE_label_text)
    CURRENT_AGE = CURRENT_AGE_col.slider(CURRENT_AGE_label_text, 18, 70, 50, label_visibility = 'collapsed')
    
    RETIREMENT_AGE_label, RETIREMENT_AGE_col = st.columns([3,4])  
    RETIREMENT_AGE_label_text = 'At what age you want to retire?'
    RETIREMENT_AGE_label.write(RETIREMENT_AGE_label_text)
    RETIREMENT_AGE = RETIREMENT_AGE_col.slider(RETIREMENT_AGE_label_text, CURRENT_AGE+1, 70, 65, label_visibility = 'collapsed')

    return CURRENT_AGE, RETIREMENT_AGE

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
      
    CURRENT_AGE, RETIREMENT_AGE = get_current_age_retirement_age_inputs()  
    
    RATE_OF_RETURN_PRE_RETIREMENT, SIP_AMOUNT_YEARLY_INCREMENT, RATE_OF_INFLATION_POST_RETIREMENT,RATE_OF_RETURN_POST_RETIREMENT = sidebar()
    
    with st.container():
        if display_options == 'a':
            find_annual_contribution_requirement()
        elif display_options == 'b':
            find_retirement_portfolio_life()
        elif display_options == 'c':
            find_retirement_corpus_life_based_on_annual_contribution()
        else:
            pass
        

