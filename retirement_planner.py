# -*- coding: utf-8 -*-
"""
Created on Fri Nov  4 18:36:44 2022

@author: Yash
"""

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

def calculate_emi(borrowed_amount, interest_rate, num_periods, remaining_balance=0,early_prepayment=False):
    emi0 = borrowed_amount / max(num_periods,1)
    if early_prepayment:
        inputs = dict(borrowed_amount=borrowed_amount, interest_rate=interest_rate, num_periods=num_periods)
    else:
        inputs = dict(borrowed_amount=borrowed_amount, interest_rate=interest_rate, num_periods=num_periods)
    #print(inputs)
    shortfall = partial(find_portfolio_shortfall_2, **inputs) 
    emi = opt.root(shortfall, x0 = emi0).x
    return emi[0]

def calculate_emi_old(target_amount, interest_rate, num_periods, remaining_balance=0,early_prepayment=False):
    emi0 = target_amount / max(num_periods,1)
    if early_prepayment:
        inputs = dict(borrowed_amount=target_amount, interest_rate=interest_rate, num_periods=num_periods)
    else:
        inputs = dict(borrowed_amount=target_amount, interest_rate=interest_rate, num_periods=num_periods)
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

def find_portfolio_shortfall_2(emi, borrowed_amount, interest_rate, num_periods):
    #print(borrowed_amount, emi, interest_rate, num_periods)
    inputs = dict(sip_amount=emi, rate_of_return=interest_rate, num_years=num_periods)    
    cumulative_fv_of_emi = get_future_value_of_SIP(**inputs)
    shortfall = borrowed_amount - cumulative_fv_of_emi
    return shortfall

def text_template(x):
    if x[3]>0:
        to_add = f'<br> - Your current portfolio of grows to $ {x[3]:,}'
    else:
        to_add = ''
    text = f"By <b>Age {x[0]}</b>,<br>Your total portfolio size will be <b>$ {x[1]:,}</b>.<br> - Your cumulative yearly contributions of $ {x[4]:,} become $ {x[2]:,} with interest."       
    return text + to_add

def plot_portfolio(future_value_of_SIP_df, x_col='t'):
    fig = go.Figure()
    
    #cols_to_plot = ['amount_invested', 'cumulative_amount_invested', 'cumulative_portfolio_size',
    #                'interest_component', 'total_portfolio_value']
    
    cols_to_plot = ['cumulative_amount_invested', 'interest_component', 'fv_of_current_balance']
    
    col_nam_to_graph_name_mapping = {'cumulative_amount_invested':'Yearly Contributions Made',
        'interest_component':'Interest Earned on Yearly Contributions',
        'fv_of_current_balance':'Value of current portfolio'}
    
    iterator = future_value_of_SIP_df[[x_col, 'total_portfolio_value']].itertuples(index=False)
    tooltips = [f'At {x_col} {age} your total portfolio = {portfolio}' \
                 for age, portfolio in iterator]
    
    customdata = future_value_of_SIP_df[['Age', 'total_portfolio_value', 'cumulative_portfolio_size',
            'fv_of_current_balance', 'cumulative_amount_invested']]

    text = [text_template(i) for i in customdata.itertuples(index=False)]
   
    for col in cols_to_plot:
        x = future_value_of_SIP_df[x_col].to_list()
        y = future_value_of_SIP_df[col].to_list()
        fig.add_trace(go.Scatter(x=x, y=y, 
                                 text = text,
                                 hoverinfo ='text',
                                 name=col_nam_to_graph_name_mapping.get(col,''),
                                 mode='lines',
                                 stackgroup='one')
                      )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(yanchor="top",y=0.99,xanchor="left", x=0.01),
        hoverlabel=dict(bgcolor="white",font_size=11,font_family="Calibri"),
        xaxis_title=f"{x_col} (Years)",
        yaxis_title="Amount ($)",
        )
    return fig

def plot_portfolio_old(future_value_of_SIP_df, x_col='t'):
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
                                 #hovertext=tooltips,
                                 name=col, mode='none')
                      )
    fig.update_layout(
        #title = 'Title',
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(yanchor="top",y=0.99,xanchor="left", x=0.01),
        hovermode='x unified',
        #hovermode='x',        
        hoverlabel=dict(bgcolor="white",font_size=11,font_family="Calibri"),
        xaxis_title=f"{x_col} (Years)",
        yaxis_title="Amount ($)",
        )
    return fig

def text_template_SWP(x):
    text = f"At <b>Age {x[0]}</b>,<br>Your retirement corpus will be <b>$ {x[1]:,}</b>"       
    return text 

def plot_swp_portfolio(tracker_df, x_col='t'):
    fig = go.Figure()
    
    cols_to_plot = ['period_end_balance']#['pre_withdrawal_balance']#, 'amount_withdrawed', 'period_end_balance']
    customdata = tracker_df[[x_col, 'period_end_balance']]
    
    text = [text_template_SWP(i) for i in customdata.itertuples(index=False)]   
    col_name_to_graph_name_mapping = {'period_end_balance':'Remaining retirement corpus value'}
    for col in cols_to_plot:
        x = tracker_df[x_col].to_list()
        y = tracker_df[col].to_list()
        fig.add_trace(go.Scatter(x=x, y=y, 
                                 text = text,
                                 hoverinfo ='text',
                                 name=col_name_to_graph_name_mapping.get(col,''),
                                 mode='lines',
                                 stackgroup='one')
                      )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(yanchor="top",y=0.99,xanchor="left", x=0.01),
        hoverlabel=dict(bgcolor="white",font_size=11,font_family="Calibri"),
        xaxis_title=f"{x_col} (Years)",
        yaxis_title="Amount ($)",
        )

    
    return fig

def plot_swp_portfolio_old(tracker_df, x_col='t'):
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

if __name__ == '__main__':
    find_how_many_years_the_account_will_last(sip_amount=1000, rate_of_return=0,
                                rate_of_SIP_increase=0.0,
                                current_balance=5000)
    
    SIP_AMOUNT_YEARLY = 10000
    SIP_AMOUNT_YEARLY_INCREMENT = 0.05
    STARTING_PORTFOLIO = 0
    
    RATE_OF_RETURN_PRE_RETIREMENT = 0.08
    
    sip_amount = 1000
    rate_of_return = 0.05
    rate_of_SIP_increase = 0
    current_balance = 10000
    
    
    
    CURRENT_AGE = 50
    RETIREMENT_AGE = 65
    
    future_value_of_SIP = get_future_value_of_SIP_at_any_point(
        sip_amount = SIP_AMOUNT_YEARLY, rate_of_return = RATE_OF_RETURN_PRE_RETIREMENT,
        num_years = RETIREMENT_AGE - CURRENT_AGE, rate_of_SIP_increase=SIP_AMOUNT_YEARLY_INCREMENT,
        current_balance=STARTING_PORTFOLIO)
    
    future_value_of_SIP_df = pd.DataFrame(future_value_of_SIP)
    
    future_value_of_SIP_df.to_csv('del.csv', index=False)
    

    io.renderers.default = 'browser'
    

    
    fig = plot_portfolio(future_value_of_SIP_df)
    fig.show()
    
    portfolio_value_at_retirement = future_value_of_SIP[-1].get('total_portfolio_value')
    
    SWP_AMOUNT_YEARLY = 1500
    RATE_OF_INFLATION_POST_RETIREMENT = 0
    RATE_OF_RETURN_POST_RETIREMENT = 0.05
    
    
    max_years, tracker = find_how_many_years_the_account_will_last(
        sip_amount = SWP_AMOUNT_YEARLY, rate_of_return = RATE_OF_RETURN_POST_RETIREMENT,
        rate_of_SIP_increase=RATE_OF_INFLATION_POST_RETIREMENT,
        current_balance=portfolio_value_at_retirement)
    
    find_how_many_years_the_account_will_last(sip_amount=1000, rate_of_return=0.05,
                                rate_of_SIP_increase=0,
                                current_balance=5000)
