# -*- coding: utf-8 -*-
"""
Created on Sun Nov  6 20:30:45 2022

@author: Yash
"""

import streamlit as st
import os

import numpy as np
import scipy.optimize as opt
  
from functools import partial
import pandas as pd

import plotly.graph_objects as go
import plotly.io as io

def future_value(current_amount, rate_of_return, num_years):
    multiplier_factor=(1+rate_of_return)**num_years
    return current_amount*multiplier_factor

def see_year_wise_fv(current_amount, rate_of_return, num_years):
    res = []
    for i in range(0,num_years+1,1):
        amt = future_value(current_amount, rate_of_return, i)
        res.append(dict(t=i, amt=amt))
    return res

def get_disounted_value(future_amount, discount_rate, num_years):
    return future_value(current_amount=future_amount,
                        rate_of_return = discount_rate,
                        num_years = -num_years)

def see_year_wise_dv(current_amount, rate_of_return, num_years):
    res = []
    for i in range(0,num_years+1,1):
        amt = get_disounted_value(current_amount, rate_of_return, i)
        res.append(dict(t=num_years-i, amt=amt))
    return res


def get_future_value_of_SIP_old(sip_amount, rate_of_return,
                            num_years, rate_of_SIP_increase=0):
    portfolio = []
    for i in range(0,num_years,1):
        fv = future_value(sip_amount*((1+rate_of_SIP_increase)**i), rate_of_return, num_years-i)
        portfolio.append(fv)
    return sum(portfolio)


def get_future_value_of_SIP(sip_amount, rate_of_return,
                            num_years, rate_of_SIP_increase=0, return_yearly_breakup=False):
    portfolio = []
    for i in range(0,num_years,1):
        amount_invested = sip_amount*((1+rate_of_SIP_increase)**i)
        fv = future_value(amount_invested, rate_of_return, num_years-i)
        res = dict(t=i, fv = fv, comment = f'at t = {num_years}')
        portfolio.append(res)
    
    if return_yearly_breakup:
        return portfolio
    else:
        return sum([i.get('fv') for i in portfolio])


def get_future_value_of_SIP_at_any_point(sip_amount, rate_of_return,
                            num_years, rate_of_SIP_increase=0,
                            current_balance=0,
                            num_payments_made=None):
    
    if num_payments_made is None:
        num_payments_made = num_years
    cumulative_portfolio_size = 0
    cumulative_amount_invested = 0
    tracker = []
    for i in range(num_years+1):
        if (i >= num_years) or (i >= num_payments_made):
            amount_invested = 0
        else:
            amount_invested = sip_amount*((1+rate_of_SIP_increase)**i)
        
        cumulative_amount_invested+=amount_invested
        if i:
            cumulative_portfolio_size=cumulative_portfolio_size*(1+rate_of_return)+amount_invested
        else:
            cumulative_portfolio_size = amount_invested
        
        fv_of_current_balance = future_value(current_balance, rate_of_return, num_years = i)
        
        interest_component = cumulative_portfolio_size- cumulative_amount_invested

        record = dict(t=i, amount_invested = amount_invested,
                  cumulative_amount_invested=cumulative_amount_invested,
                  cumulative_portfolio_size=cumulative_portfolio_size,
                  interest_component=interest_component,
                  fv_of_current_balance=fv_of_current_balance,
                  total_portfolio_value=fv_of_current_balance+cumulative_portfolio_size)

        tracker.append(record)
    return tracker

def get_future_value_of_SWP_at_any_point(sip_amount, rate_of_return,
                            num_years, rate_of_SIP_increase=0,
                            current_balance=0):
    tracker = []
    for i in range(num_years+1):
        if i != 0:
            pre_withdrawal_balance = current_balance*(1+rate_of_return)
            amount_withdrawed = sip_amount*((1+rate_of_SIP_increase)**(i-1)) 
        else:
            pre_withdrawal_balance = current_balance
            amount_withdrawed = 0
        
        period_end_balance = pre_withdrawal_balance - amount_withdrawed
        current_balance = period_end_balance
        record  = dict(t=i, pre_withdrawal_balance=pre_withdrawal_balance,
                       amount_withdrawed=amount_withdrawed,
                       period_end_balance=period_end_balance)
        tracker.append(record)
    
    return tracker

get_future_value_of_SWP_at_any_point(sip_amount=1000, rate_of_return=0.05,
                            num_years=10, rate_of_SIP_increase=0.05,
                            current_balance=10000)

def find_how_many_years_the_account_will_last(sip_amount, rate_of_return,
                            rate_of_SIP_increase=0,
                            current_balance=0):
    input_dict = dict(sip_amount=sip_amount, rate_of_return=rate_of_return,
                            rate_of_SIP_increase=rate_of_SIP_increase,
                            current_balance=current_balance)
    swp_function = partial(get_future_value_of_SWP_at_any_point, **input_dict)   
    max_years = 100
    for i in range(1,max_years,1):
        tracker = swp_function(num_years=i)
        if tracker[-1].get('period_end_balance')<0:
            max_years=i-1
            break
    
    return max_years, tracker

def calculate_emi(borrowed_amount, interest_rate, num_periods, remaining_balance=0):
    emi0 = borrowed_amount / num_periods
    inputs = dict(borrowed_amount=borrowed_amount, interest_rate=interest_rate, num_periods=num_periods)
    #print(inputs)
    shortfall = partial(find_portfolio_shortfall, **inputs) 
    emi = opt.root(shortfall, x0 = emi0).x
    return emi[0]

def find_portfolio_shortfall(emi, borrowed_amount, interest_rate, num_periods):
    #print(borrowed_amount, emi, interest_rate, num_periods)
    amount_borrowed_fv = future_value(borrowed_amount, interest_rate, num_periods)
    inputs = dict(sip_amount=emi, rate_of_return=interest_rate, num_years=num_periods)    
    cumulative_fv_of_emi = get_future_value_of_SIP(**inputs)
    shortfall = amount_borrowed_fv - cumulative_fv_of_emi
    return shortfall

def plot_portfolio(future_value_of_SIP_df, x_col='t'):
    fig = go.Figure()
    
    cols_to_plot = ['amount_invested', 'cumulative_amount_invested', 'cumulative_portfolio_size',
                    'interest_component', 'total_portfolio_value']
    
    iterator = future_value_of_SIP_df[[x_col, 'total_portfolio_value']].itertuples(index=False)
    tooltips = [f'At {x_col} {age} your total portfolio = {portfolio}' \
                 for age, portfolio in iterator]
    
    for col in cols_to_plot:
        x = future_value_of_SIP_df[x_col].to_list()
        y = future_value_of_SIP_df[col].to_list()
        fig.add_trace(go.Scatter(x=x, y=y, fill = 'tozeroy', 
                                 text = [round(i,0) for i in y],
                                 hoverinfo ='text',
                                 hovertext=tooltips,
                                 name=col, mode='none')
                      )
    fig.update_layout(
        #title = 'Title',
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(yanchor="top",y=0.99,xanchor="left", x=0.01),
        #hovermode='x unified',
        hovermode='x',        
        hoverlabel=dict(bgcolor="white",font_size=11,font_family="Calibri"),
        xaxis_title=f"{x_col} (Years)",
        yaxis_title="Amount ($)",
        )
    return fig

def plot_swp_portfolio(tracker_df, x_col='t'):
    fig = go.Figure()
    
    cols_to_plot = ['period_end_balance']#['pre_withdrawal_balance']#, 'amount_withdrawed', 'period_end_balance']
    
    #iterator = future_value_of_SIP_df[[x_col, 'total_portfolio_value']].itertuples(index=False)
    #tooltips = [f'At {x_col} {age} your total portfolio = {portfolio}' \
    #             for age, portfolio in iterator]
    
    for col in cols_to_plot:
        x = tracker_df[x_col].to_list()
        y = tracker_df[col].to_list()
        fig.add_trace(go.Scatter(x=x, y=y, fill = 'tozeroy', 
                                 text = [round(i,0) for i in y],
                                 #hoverinfo ='text',
                                 #hovertext=tooltips,
                                 name=col, mode='none')
                      )
    fig.update_layout(
        #title = 'Title',
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(yanchor="top",y=0.99,xanchor="right", x=0.01),
        #hovermode='x unified',
        hovermode='x',        
        hoverlabel=dict(bgcolor="white",font_size=11,font_family="Calibri"),
        xaxis_title=f"{x_col} (Years)",
        yaxis_title="Amount ($)",
        )
    
    return fig

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
      pass

    
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
        

