import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from datetime import datetime
from datetime import timedelta

import requests
from bs4 import BeautifulSoup

try:
    # Lấy danh sách mã Việt Nam
    def get_stock(url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', class_='wikitable collapsible autocollapse sortable')
            if table:
                stock_data = []
                # Duyệt qua mỗi hàng trong bảng
                for row in table.find_all('tr')[2:]:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) > 0:  # Kiểm tra xem dòng có dữ liệu không
                        # Lấy dữ liệu từ mỗi ô trong hàng
                        row_data = [col.text.strip() for col in cols]
                        if row_data[2] == 'HSX':
                            stock_data.append(row_data)
                        else:
                            continue
                return stock_data
            else:
                return None
        else:
            return None


    # Thay thế 'url' bằng URL thực sự mà bạn muốn lấy danh sách từ
    url = 'https://vi.wikipedia.org/wiki/Danh_s%C3%A1ch_c%C3%B4ng_ty_tr%C3%AAn_s%C3%A0n_giao_d%E1%BB%8Bch_ch%E1%BB%A9ng_kho%C3%A1n_Vi%E1%BB%87t_Nam'
    stock_symbols = get_stock(url)

    # Lấy danh sách các mã cổ phiếu từ cột đầu tiên của bảng dữ liệu
    VN_stock_list = [row[0] for row in stock_symbols]

    # Tạo hộp chọn trong sidebar để chọn mã cổ phiếu

    ticker = None
    tick = st.sidebar.text_input('Ticker', value=None)
    option_tick = st.sidebar.selectbox("Mã Việt Nam", VN_stock_list, index=None, placeholder="Chọn mã")

    if not tick and not option_tick:
        ticker = None
        st.title('WELCOME TO OUR WEBSITE')
    elif not tick and not option_tick:
        ticker = None
        st.title('WELCOME TO OUR WEBSITE')
    elif tick and not option_tick:
        ticker = tick
    elif not tick and option_tick:
        ticker = option_tick + '.VN'
    elif tick and option_tick:
        ticker = None  # Reset ticker to None if both tick and option_tick have values
        st.subheader('Lưu ý chỉ chọn một mã chứng khoán')

    if ticker is not None:
        caplock_ticker = ticker.title().upper()
        st.title(caplock_ticker)
        mck = yf.Ticker(ticker)
        st.subheader(mck.info['longName'])

        bsheet = mck.balance_sheet
        income = mck.income_stmt
        cfs = mck.cashflow
        statistic = mck.info
        years = bsheet.columns[-5:]  # 4 cột cho 4 năm và 1 cột cho TTM

        if bsheet.empty:
            st.caption('Không tìm thấy thông tin')

        elif income.empty:
            st.caption('Không tìm thấy thông tin')

        elif cfs.empty:
            st.caption('Không tìm thấy thông tin')

        else:
            quarter_bsheet = mck.quarterly_balance_sheet
            first_column_index = quarter_bsheet.columns[0]
            TTM_bsheet = quarter_bsheet[first_column_index]
            second_column_index = quarter_bsheet.columns[1]
            TTM_bsheet2 = quarter_bsheet[second_column_index]
            TTM_bsheet3 = quarter_bsheet.iloc[:, :4].sum(axis=1)
            five_column_index = quarter_bsheet.columns[len(quarter_bsheet.columns) - 1]
            TTM_bsheet4 = quarter_bsheet[five_column_index]

            quarter_income = mck.quarterly_income_stmt
            TTM = quarter_income.iloc[:, :4].sum(axis=1)

            quarter_cfs = mck.quarterly_cashflow
            TTM_cfs = quarter_cfs.iloc[:, :4].sum(axis=1)

            # F-score
            # Score #1 - change in Total Revenue (Thay đổi doanh thu)
            revenue_values = [income[year]['Total Revenue'] for year in years[::-1]]
            rv_scores = [1 if revenue_values[i] < revenue_values[i + 1] else 0 for i in
                         range(len(revenue_values) - 1)]
            annual_rv_score = sum(rv_scores)
            TTM_rv_score = 1 if TTM['Total Revenue'] > income[years[-(len(revenue_values) - 1)]][
                'Total Revenue'] else 0
            total_rv_score = annual_rv_score + TTM_rv_score

            # Score #2 - change in Net Income (Thay đổi lợi nhuận)
            ni_values = [income[year]['Net Income'] for year in years[::-1]]
            ni_scores = [1 if ni_values[i] < ni_values[i + 1] else 0 for i in range(len(ni_values) - 1)]
            annual_ni_score = sum(ni_scores)
            TTM_ni_score = 1 if TTM['Net Income'] > income[years[-(len(revenue_values) - 1)]][
                'Net Income'] else 0
            total_ni_score = annual_ni_score + TTM_ni_score

            # Score #3 - change in Operating Cash Flow (Thay đổi dòng tiền đầu tư)
            opcf_values = [cfs[year]['Operating Cash Flow'] for year in years[::-1]]
            opcf_scores = [1 if opcf_values[i] < opcf_values[i + 1] else 0 for i in range(len(opcf_values) - 1)]
            annual_opcf_score = sum(opcf_scores)
            TTM_opcf_score = 1 if TTM_cfs['Operating Cash Flow'] > cfs[years[-(len(revenue_values) - 1)]][
                'Operating Cash Flow'] else 0
            total_opcf_score = annual_opcf_score + TTM_opcf_score

            # Score #4 - change in Free Cash Flow
            fcf_values = [cfs[year]['Free Cash Flow'] for year in years[::-1]]
            fcf_scores = [1 if fcf_values[i] < fcf_values[i + 1] else 0 for i in range(len(fcf_values) - 1)]
            annual_fcf_score = sum(fcf_scores)
            TTM_fcf_score = 1 if TTM_cfs['Free Cash Flow'] > cfs[years[-(len(revenue_values) - 1)]][
                'Free Cash Flow'] else 0
            total_fcf_score = annual_fcf_score + TTM_fcf_score

            # Score #5 - change in EPS
            eps_values = [income[year]['Basic EPS'] for year in years[::-1]]
            eps_scores = [1 if eps_values[i] < eps_values[i + 1] else 0 for i in range(len(eps_values) - 1)]
            annual_eps_score = sum(eps_scores)
            TTM_eps_score = 1 if TTM['Basic EPS'] > income[years[-(len(revenue_values) - 1)]][
                'Basic EPS'] else 0
            total_eps_score = annual_eps_score + TTM_eps_score

            # Score #6 - change in ROE
            roe_values = [income[year]['Net Income'] / bsheet[year]['Total Equity Gross Minority Interest']
                          for year in years[::-1]]
            roe_scores = [1 if roe_values[i] < roe_values[i + 1] else 0 for i in range(len(roe_values) - 1)]
            annual_roe_score = sum(roe_scores)
            TTM_roe_score = 1 if TTM['Net Income'] / TTM_bsheet['Total Equity Gross Minority Interest'] > \
                                 income[years[-(len(revenue_values) - 1)]][
                                     'Net Income'] / bsheet[years[-(len(revenue_values) - 1)]][
                                     'Total Equity Gross Minority Interest'] else 0
            total_roe_score = annual_roe_score + TTM_roe_score

            # Score #7 - change in Current Ratio
            cr_ratio_history = [bsheet[year]['Current Assets'] / bsheet[year]['Current Liabilities'] for year in
                                years[::-1]]
            cr_scores = [1 if cr_ratio_history[i] < cr_ratio_history[i + 1] else 0 for i in
                         range(len(cr_ratio_history) - 1)]
            annual_cr_score = sum(cr_scores)
            TTM_cr_score = 1 if TTM_bsheet['Current Assets'] / TTM_bsheet['Current Liabilities'] > \
                                bsheet[years[-(len(revenue_values) - 1)]][
                                    'Current Assets'] / bsheet[years[-(len(revenue_values) - 1)]][
                                    'Current Liabilities'] else 0
            total_cr_score = annual_cr_score + TTM_cr_score

            # Score #8 - change in Debt to Equity Ratio
            der_values = [bsheet[year]['Total Debt'] / bsheet[year]['Total Equity Gross Minority Interest'] for
                          year
                          in
                          years[::-1]]
            der_scores = [1 if der_values[i] > der_values[i + 1] else 0 for i in range(len(der_values) - 1)]
            annual_der_score = sum(der_scores)
            TTM_der_score = 1 if TTM_bsheet['Total Debt'] / TTM_bsheet['Total Equity Gross Minority Interest'] < \
                                 bsheet[years[-(len(revenue_values) - 1)]][
                                     'Total Debt'] / bsheet[years[-(len(revenue_values) - 1)]][
                                     'Total Equity Gross Minority Interest'] else 0
            total_der_score = annual_der_score + TTM_der_score

            # Score #9 - change in Accounts Receivable
            ar_values = [bsheet[year]['Accounts Receivable'] for year in years[::-1]]
            ar_scores = [1 if ar_values[i] > ar_values[i + 1] else 0 for i in range(len(ar_values) - 1)]
            annual_ar_score = sum(ar_scores)
            TTM_ar_score = 1 if TTM_bsheet['Accounts Receivable'] < bsheet[years[-(len(revenue_values) - 1)]][
                'Accounts Receivable'] else 0
            total_ar_score = annual_ar_score + TTM_ar_score

            # Calculate the total score
            total_score = total_rv_score + total_ni_score + total_opcf_score + total_fcf_score + total_roe_score + total_eps_score + total_cr_score + total_der_score + total_ar_score

            # GURU
            # Liquidity + Dividend
            cr_ratio = round((TTM_bsheet['Current Assets'] / TTM_bsheet['Current Liabilities']), 2)
            # Lấy dữ liệu từ năm trước đến năm hiện tại

            # Tính toán giá trị min-max
            min_cr_ratio = round(min(cr_ratio_history), 2)
            max_cr_ratio = round(max(cr_ratio_history), 2)

            qr_ratio = round(((TTM_bsheet['Current Assets'] - TTM_bsheet['Inventory']) / TTM_bsheet['Current Liabilities']),
                             2) if 'Inventory' in TTM_bsheet else TTM_bsheet['Current Assets'] / TTM_bsheet[
                'Current Liabilities']
            qr_ratio_history = [(bsheet.loc['Current Assets', year] - bsheet.loc['Inventory', year]) / (bsheet.loc['Current Liabilities', year]) if 'Inventory' in bsheet
                                else bsheet.loc['Current Assets', year] / (bsheet.loc['Current Liabilities', year]) for year in years[::-1]]

            # Tính toán giá trị min-max
            min_qr_ratio = round(min(qr_ratio_history), 2)
            max_qr_ratio = round(max(qr_ratio_history), 2)

            car_ratio = round((TTM_bsheet['Cash And Cash Equivalents'] / TTM_bsheet['Current Liabilities']), 2)
            car_ratio_history = [
                bsheet.loc['Cash And Cash Equivalents', year] / (bsheet.loc['Current Liabilities', year] or 1) for year in
                years[::-1]]

            # Tính toán giá trị min-max
            min_car_ratio = round(min(car_ratio_history), 2)
            max_car_ratio = round(max(car_ratio_history), 2)

            dso_ratio = round((TTM_bsheet['Accounts Receivable'] / TTM['Total Revenue']) * 365, 2)
            dso_ratio_history = [
                bsheet.loc['Accounts Receivable', year] / (income.loc['Total Revenue', year] or 1) for year in
                years[::-1]]
            # Tính toán giá trị min-max
            min_dso_ratio = round(min(dso_ratio_history), 2)
            max_dso_ratio = round(max(dso_ratio_history), 2)

            ap_average_values = (TTM_bsheet4['Accounts Payable'] + TTM_bsheet['Accounts Payable']) / 2
            dp_ratio = round((ap_average_values / TTM['Cost Of Revenue']) * 365, 2)
            dp_ratio_history = [bsheet.loc['Accounts Payable', year] * 365 / (income.loc['Cost Of Revenue', year] or 1)
                                for year in years[::-1]]
            # Tính toán giá trị min-max
            min_dp_ratio = round(min(dp_ratio_history), 2)
            max_dp_ratio = round(max(dp_ratio_history), 2)

            if 'Inventory' in TTM_bsheet:

                inv_average = (TTM_bsheet4['Inventory'] + TTM_bsheet['Inventory']) / 2
                dio_ratio = round((inv_average / TTM['Cost Of Revenue']) * 365, 2)
                dio_ratio_history = [bsheet.loc['Inventory', year] * 365 / (income.loc['Cost Of Revenue', year] or 1) for
                                 year in years[::-1]]
                # Tính toán giá trị min-max
                min_dio_ratio = round(min(dio_ratio_history), 2)
                max_dio_ratio = round(max(dio_ratio_history), 2)
                dio_values = (dio_ratio - min_dio_ratio) / (max_dio_ratio - min_dio_ratio)
            else:
                dio_values = 0
                dio_ratio = 0

            div_ratio = mck.info['trailingAnnualDividendYield'] * 100 if 'trailingAnnualDividendYield' in statistic else 0
            pr_ratio = mck.info['payoutRatio'] if 'payoutRatio' in statistic else 0
            five_years_ratio = mck.info['fiveYearAvgDividendYield'] if 'fiveYearAvgDividendYield' in statistic else 0
            forward_ratio = mck.info['dividendYield'] * 100 if 'dividendYield' in statistic else 0
            cr_values2 = (cr_ratio - min_cr_ratio) / (max_cr_ratio - min_cr_ratio)
            qr_values = (qr_ratio - min_qr_ratio) / (max_qr_ratio - min_qr_ratio)
            car_values = (car_ratio - min_car_ratio) / (max_car_ratio - min_car_ratio)
            dso_values = (dso_ratio - min_dso_ratio) / (max_dso_ratio - min_dso_ratio)
            dp_values = (dp_ratio - min_dp_ratio) / (max_dp_ratio - min_dp_ratio)
            div_values = 0
            pr_values = 0
            five_years_values = 0
            forward_values = 0
            # PE Ratio
            shares_outstanding = mck.info['sharesOutstanding']
            PE_ratio = mck.info['trailingPE']
            pe_ratio_history = [(bsheet.loc['Total Capitalization', year] / bsheet.loc['Share Issued', year]) / (
                income.loc['Basic EPS', year]) for year in years[::-1]]
            min_pe_ratio = round(min(pe_ratio_history), 2)
            max_pe_ratio = round(max(pe_ratio_history), 2)
            PE_ratio2 = (PE_ratio - min_pe_ratio) / (max_pe_ratio - min_pe_ratio)

            # P/S Ratio
            PS_ratio = mck.info['currentPrice'] / mck.info["revenuePerShare"]
            ps_ratio_history = [(bsheet.loc['Total Capitalization', year] / bsheet.loc['Share Issued', year]) / (
                    income.loc['Total Revenue', year] / bsheet.loc['Share Issued', year]) for year in years[::-1]]
            min_ps_ratio = round(min(ps_ratio_history), 2)
            max_ps_ratio = round(max(ps_ratio_history), 2)
            PS_ratio2 = (PS_ratio - min_ps_ratio) / (max_ps_ratio - min_ps_ratio)

            # P/B Ratio
            PB_ratio = mck.info['priceToBook']
            pb_ratio_history = [
                bsheet.loc['Stockholders Equity', year] / (income.loc['Net Income', year] / income.loc['Basic EPS', year])
                for year in years[::-1]]
            min_pb_ratio = round(min(pb_ratio_history), 2)
            max_pb_ratio = round(max(pb_ratio_history), 2)
            PB_ratio2 = (PB_ratio - min_pb_ratio) / (max_pb_ratio - min_pb_ratio)

            # Price-to-tangible-book Ratio
            Price_to_TBV = mck.info['currentPrice'] / (TTM_bsheet['Tangible Book Value'] / shares_outstanding)
            Price_to_TBV_history = [(bsheet.loc['Total Capitalization', year] / bsheet.loc['Share Issued', year]) / (
                    bsheet.loc['Tangible Book Value', year] / bsheet.loc['Share Issued', year]) for year in years[::-1]]
            min_Price_to_TBV_ratio = round(min(Price_to_TBV_history), 2)
            max_Price_to_TBV_ratio = round(max(Price_to_TBV_history), 2)
            if max_Price_to_TBV_ratio == min_Price_to_TBV_ratio:
                Price_to_TBV2 = 0
            else:
                Price_to_TBV2= (Price_to_TBV - min_Price_to_TBV_ratio) / (max_Price_to_TBV_ratio - min_Price_to_TBV_ratio)

            # Price-to-Free-Cash_Flow Ratio
            price_to_FCF = mck.info['currentPrice'] / (TTM_cfs['Free Cash Flow'] / shares_outstanding)
            Price_to_FCF_history = [(bsheet.loc['Total Capitalization', year] / bsheet.loc['Share Issued', year]) / (
                    cfs.loc['Free Cash Flow', year] / bsheet.loc['Share Issued', year]) for year in years[::-1]]
            min_price_to_FCF_ratio = round(min(Price_to_FCF_history), 2)
            max_price_to_FCF_ratio = round(max(Price_to_FCF_history), 2)
            price_to_FCF2 = (price_to_FCF - min_price_to_FCF_ratio) / (max_price_to_FCF_ratio - min_price_to_FCF_ratio)

            # EV-to-EBIT
            EV_to_EBIT = mck.info['enterpriseValue'] / TTM['EBIT']
            EV_to_EBIT_history = [(bsheet.loc['Total Capitalization', year] - bsheet.loc[
                'Total Liabilities Net Minority Interest', year] - bsheet.loc[
                                       'Cash Cash Equivalents And Short Term Investments', year]) / (
                                      income.loc['EBIT', year]) for year in years[::-1]]
            min_EV_to_EBIT_ratio = round(min(EV_to_EBIT_history), 2)
            max_EV_to_EBIT_ratio = round(max(EV_to_EBIT_history), 2)
            EV_to_EBIT2 = (EV_to_EBIT - min_EV_to_EBIT_ratio) / (max_EV_to_EBIT_ratio - min_EV_to_EBIT_ratio)

            # EV-to-EBITDA
            EV_to_EBITDA = mck.info['enterpriseValue'] / TTM['EBITDA']
            EV_to_EBITDA_history = [(bsheet.loc['Total Capitalization', year] - bsheet.loc[
                'Total Liabilities Net Minority Interest', year] - bsheet.loc[
                                         'Cash Cash Equivalents And Short Term Investments', year]) / (
                                        income.loc['EBITDA', year]) for year in years[::-1]]
            min_EV_to_EBITDA_ratio = round(min(EV_to_EBITDA_history), 2)
            max_EV_to_EBITDA_ratio = round(max(EV_to_EBITDA_history), 2)
            EV_to_EBITDA2 = (EV_to_EBITDA - min_EV_to_EBITDA_ratio) / (max_EV_to_EBITDA_ratio - min_EV_to_EBITDA_ratio)

            # EV-to-Revenue
            EV_to_Revenue = mck.info['enterpriseValue'] / TTM['Total Revenue']
            EV_to_Revenue_history = [(bsheet.loc['Total Capitalization', year] - bsheet.loc[
                'Total Liabilities Net Minority Interest', year] - bsheet.loc[
                                          'Cash Cash Equivalents And Short Term Investments', year]) / (
                                         income.loc['Total Revenue', year]) for year in years[::-1]]
            min_EV_to_Revenue_ratio = round(min(EV_to_Revenue_history), 2)
            max_EV_to_Revenue_ratio = round(max(EV_to_Revenue_history), 2)
            EV_to_Revenue2 = (EV_to_Revenue - min_EV_to_Revenue_ratio) / (max_EV_to_Revenue_ratio - min_EV_to_Revenue_ratio)

            # EV-to-FCF
            EV_to_FCF = mck.info['enterpriseValue'] / TTM_cfs['Free Cash Flow']
            EV_to_FCF_history = [(bsheet.loc['Total Capitalization', year] - bsheet.loc[
                'Total Liabilities Net Minority Interest', year] - bsheet.loc[
                                      'Cash Cash Equivalents And Short Term Investments', year]) / (
                                     cfs.loc['Free Cash Flow', year]) for year in years[::-1]]
            min_EV_to_FCF_ratio = round(min(EV_to_FCF_history), 2)
            max_EV_to_FCF_ratio = round(max(EV_to_FCF_history), 2)
            EV_to_FCF2 = (EV_to_FCF - min_EV_to_FCF_ratio) / (max_EV_to_FCF_ratio - min_EV_to_FCF_ratio)

            # Price-to-Net-Current-Asset-Value
            Price_to_Net_CAV = mck.info['currentPrice'] / (
                        (TTM_bsheet['Current Assets'] - TTM_bsheet['Current Liabilities']) / shares_outstanding)
            Price_to_Net_CAV_history = [(bsheet.loc['Total Capitalization', year] / bsheet.loc['Share Issued', year]) / (
                        (bsheet.loc['Current Assets', year] - bsheet.loc['Current Liabilities', year])
                        / bsheet.loc['Share Issued', year]) for year in years[::-1]]
            min_Price_to_Net_CAV_ratio = round(min(Price_to_Net_CAV_history), 2)
            max_Price_to_Net_CAV_ratio = round(max(Price_to_Net_CAV_history), 2)
            Price_to_Net_CAV2 = (Price_to_Net_CAV - min_Price_to_Net_CAV_ratio) / (
                        max_Price_to_Net_CAV_ratio - min_Price_to_Net_CAV_ratio)

            # Earnings Yields (Greenblatt) %
            EarningsYields = (TTM['EBIT'] / mck.info['enterpriseValue']) * 100
            EarningsYields_history = [((income.loc['EBIT', year] / (bsheet.loc['Total Capitalization', year] - bsheet.loc[
                'Total Liabilities Net Minority Interest', year] - bsheet.loc[
                                                                    'Cash Cash Equivalents And Short Term Investments', year])) * 100)
                                      for year in years[::-1]]
            min_EarningsYields_ratio = round(min(EarningsYields_history), 2)
            max_EarningsYields_ratio = round(max(EarningsYields_history), 2)
            EarningsYields2 = (EarningsYields - min_EarningsYields_ratio) / (
                        max_EarningsYields_ratio - min_EarningsYields_ratio)

            # FCF Yield %
            FCFYield = (TTM_cfs['Free Cash Flow'] / mck.info['marketCap']) * 100 if 'marketCap' in mck.info else (TTM_cfs['Free Cash Flow']/mck.basic_info['marketCap'])*100
            FCFYield_history = [((cfs.loc['Free Cash Flow', year] / bsheet.loc['Total Capitalization', year]) * 100) for year in
                                years[::-1]]
            min_FCFYield_ratio = round(min(FCFYield_history), 2)
            max_FCfYield_ratio = round(max(FCFYield_history), 2)
            FCFYield2 = (FCFYield - min_FCFYield_ratio) / (max_FCfYield_ratio - min_FCFYield_ratio)

            # Profitability Rank
            # Gross Margin %
            gr_margin = round((TTM['Gross Profit'] * 100 / TTM['Total Revenue']), 2)
            gr_margin_history = [
                income.loc['Gross Profit', year] * 100 / (income.loc['Total Revenue', year] or 1) for year in
                years[::-1]]
            # Tìm min max
            min_gr_margin = round(min(gr_margin_history), 2)
            max_gr_margin = round(max(gr_margin_history), 2)

            # Operating Margin %
            op_margin = round((TTM['Operating Income'] * 100 / TTM['Total Revenue']), 2)
            op_margin_history = [
                income.loc['Operating Income', year] * 100 / (income.loc['Total Revenue', year] or 1) for year in
                years[::-1]]
            # Tìm min max
            min_op_margin = round(min(op_margin_history), 2)
            max_op_margin = round(max(op_margin_history), 2)

            # Net Margin %
            net_margin = round((TTM['Net Income'] * 100 / TTM['Total Revenue']), 2)
            net_margin_history = [
                income.loc['Net Income', year] * 100 / (income.loc['Total Revenue', year] or 1) for year in
                years[::-1]]
            # Tìm min max
            min_net_margin = round(min(net_margin_history), 2)
            max_net_margin = round(max(net_margin_history), 2)

            # FCF margin %
            fcf_margin = round((TTM_cfs['Free Cash Flow'] * 100 / TTM['Total Revenue']), 2)
            fcf_margin_history = [
                cfs.loc['Free Cash Flow', year] * 100 / (income.loc['Total Revenue', year] or 1) for year in
                years[::-1]]
            # Tìm min max
            min_fcf_margin = round(min(fcf_margin_history), 2)
            max_fcf_margin = round(max(fcf_margin_history), 2)

            # ROE%
            roe_stock_average = (TTM_bsheet2['Total Equity Gross Minority Interest'] + TTM_bsheet[
                'Total Equity Gross Minority Interest']) / 2
            roe_margin = round((TTM['Net Income'] * 100 / roe_stock_average), 2)
            roe_margin_history = [
                income.loc['Net Income', year] * 100 / (bsheet.loc['Total Equity Gross Minority Interest', year] or 1)
                for year in years[::-1]]
            # Tìm min max
            min_roe_margin = round(min(roe_margin_history), 2)
            max_roe_margin = round(max(roe_margin_history), 2)

            # ROA%
            roa_tta_average = (TTM_bsheet2['Total Assets'] + TTM_bsheet['Total Assets']) / 2
            roa_margin = round((TTM['Net Income'] * 100 / roa_tta_average), 2)
            roa_margin_history = [income.loc['Net Income', year] * 100 / (bsheet.loc['Total Assets', year] or 1)
                                  for year in years[::-1]]
            # Tìm min max
            min_roa_margin = round(min(roa_margin_history), 2)
            max_roa_margin = round(max(roa_margin_history), 2)

            # ROC (Joel Greenblatt) %
            fix_work_average = (TTM_bsheet['Net Tangible Assets'] + TTM_bsheet['Working Capital']) / 2
            roc_margin = round((TTM['EBIT'] * 100 / fix_work_average), 2)
            roc_margin_history = [income.loc['EBIT', year] * 100 / (
                        (bsheet.loc['Net Tangible Assets', year] + bsheet.loc['Working Capital', year]) / 2 or 1)
                                  for year in years[::-1]]
            # Tìm min max
            min_roc_margin = round(min(roc_margin_history), 2)
            max_roc_margin = round(max(roc_margin_history), 2)

            # ROCE%
            cap_em_1 = (TTM_bsheet['Total Assets'] - TTM_bsheet['Current Liabilities'])
            cap_em_2 = (TTM_bsheet2['Total Assets'] - TTM_bsheet2['Current Liabilities'])
            cap_em_average = (cap_em_1 + cap_em_2) / 2
            roce_margin = round((TTM['EBIT'] * 100 / cap_em_average), 2)
            roce_margin_history = [income.loc['EBIT', year] * 100 / (
                        bsheet.loc['Total Assets', year] - bsheet.loc['Current Liabilities', year] or 1)
                                   for year in years[::-1]]
            # Tìm min max
            min_roce_margin = round(min(roce_margin_history), 2)
            max_roce_margin = round(max(roce_margin_history), 2)

            gr_values = (gr_margin - min_gr_margin) / (max_gr_margin - min_gr_margin)
            op_values = (op_margin - min_op_margin) / (max_op_margin - min_op_margin)
            net_values = (net_margin - min_net_margin) / (max_net_margin - min_net_margin)
            fcf_ma_values = (fcf_margin - min_fcf_margin) / (max_fcf_margin - min_fcf_margin)
            roe_ma_values = (roe_margin - min_roe_margin) / (max_roe_margin - min_roe_margin)
            roa_values = (roa_margin - min_roa_margin) / (max_roa_margin - min_roa_margin)
            roc_values = (roc_margin - min_roc_margin) / (max_roc_margin - min_roc_margin)
            roce_values = (roce_margin - min_roce_margin) / (max_roce_margin - min_roce_margin)

            #Financial Strength

            #Cash_to_debt
            cash_debt = TTM_bsheet['Cash Cash Equivalents And Short Term Investments']/TTM_bsheet['Total Debt']
            cash_debt_history = [bsheet.loc['Cash Cash Equivalents And Short Term Investments', year]/ (bsheet.loc['Total Debt', year] or 1) for year in
                years[::-1]]
            # Tìm min max
            min_cash_debt = round(min(cash_debt_history), 2)
            max_cash_debt = round(max(cash_debt_history), 2)

            #Equity to Asset
            equity_asset = TTM_bsheet['Stockholders Equity']/TTM_bsheet['Total Assets']
            equity_asset_history = [bsheet.loc['Stockholders Equity', year]/ (bsheet.loc['Total Assets', year] or 1) for year in
                years[::-1]]
            # Tìm min max
            min_equity_asset = round(min(equity_asset_history), 2)
            max_equity_asset = round(max(equity_asset_history), 2)

            #Debt to Equity
            debt_equity = TTM_bsheet['Total Debt']/TTM_bsheet['Stockholders Equity']
            debt_equity_history = [bsheet.loc['Total Debt', year]/ (bsheet.loc['Stockholders Equity', year] or 1) for year in
                years[::-1]]
            # Tìm min max
            min_debt_equity = round(min(debt_equity_history), 2)
            max_debt_equity = round(max(debt_equity_history), 2)

            #Debt to EBITDA
            debt_ebitda = TTM_bsheet['Total Debt']/TTM['EBITDA'] if 'Total Debt' in TTM_bsheet else 0
            debt_ebitda_history = [bsheet.loc['Total Debt', year]/ (income.loc['EBITDA', year] or 1) for year in
                years[::-1]]
            # Tìm min max
            min_debt_ebitda = round(min(debt_ebitda_history), 2)
            max_debt_ebitda = round(max(debt_ebitda_history), 2)

            #Interest Coverage
            interest_coverage = TTM['Operating Income']/TTM['Interest Expense'] if 'Interest Expense' in TTM else 0
            interest_coverage_history = [income.loc['Operating Income', year]/ (income.loc['Interest Expense', year] or 1) for year in
                years[::-1]]
            # Tìm min max
            min_interest_coverage = round(min(interest_coverage_history), 2)
            max_interest_coverage = round(max(interest_coverage_history), 2)

            cash_debt_values = (cash_debt - min_cash_debt) / (max_cash_debt - min_cash_debt)
            equity_asset_values = (equity_asset - min_equity_asset) / (max_equity_asset - min_equity_asset)
            debt_equity_values = (debt_equity - min_debt_equity) / (max_debt_equity - min_debt_equity)
            debt_ebitda_values = (debt_ebitda - min_debt_ebitda) / (max_debt_ebitda - min_debt_ebitda)
            interest_coverage_values = (interest_coverage - min_interest_coverage) / (max_interest_coverage - min_interest_coverage)

            #Altman F-Score
            a = TTM_bsheet['Working Capital']/TTM_bsheet['Total Assets']
            b = TTM_bsheet['Retained Earnings']/TTM_bsheet['Total Assets']
            c = TTM['EBIT']/TTM_bsheet['Total Assets']
            d = mck.info['marketCap']/TTM_bsheet['Total Liabilities Net Minority Interest'] if 'marketCap' in mck.info else mck.basic_info['marketCap']/TTM_bsheet['Total Liabilities Net Minority Interest']
            e = TTM['Total Revenue']/TTM_bsheet['Total Assets']
            altmanz_score = 1.2*a+1.4*b+3.3*c+0.6*d+e

            #Piotroski F-Score
            # Score #1 - ROA
            roa_score = 1 if TTM['Net Income'] > 0 else 0

            # Score #2 - Operating Cash Flow
            ocf_score = 1 if TTM_cfs['Operating Cash Flow'] > 0 else 0

            # Score #3 - change in ROA
            roa_1 = TTM['Net Income']/TTM_bsheet4['Total Assets']
            roa_2 = income[years[1-len(years)]]['Net Income']/bsheet[years[2-len(years)]]['Total Assets']
            croa_score = 1 if roa_1 > roa_2 else 0

            # Score #4 - Quality of Earnings (Accrual)
            acc_score = 1 if TTM_cfs['Operating Cash Flow'] > TTM['Net Income'] else 0

            # Score #5 - Leverage (long term debt/average total assets) (Moi lay 2 quy gan nhat 2022, yf khum co)
            t_assets = quarter_bsheet.sum(axis=1)
            ave_assets = t_assets/5
            lv_1 = TTM_bsheet['Long Term Debt And Capital Lease Obligation'] / ave_assets['Total Assets'] if 'Long Term Debt And Capital Lease Obligation' in TTM_bsheet else 0
            pre_assets = 1/2 * (bsheet[years[1-len(years)]]['Total Assets'] + TTM_bsheet4['Total Assets'])
            lv_2 = TTM_bsheet4['Long Term Debt And Capital Lease Obligation'] / pre_assets if 'Long Term Debt And Capital Lease Obligation' in TTM_bsheet4 else 0
            lv_score = 0 if lv_1 > lv_2 else 1


            # Score #6 - change in Working Capital (Liquidity)
            cr_1 = TTM_bsheet['Current Assets'] / TTM_bsheet['Current Liabilities']
            cr_2 = bsheet[years[1-len(years)]]['Current Assets'] / bsheet[years[1-len(years)]]['Current Liabilities']
            cr_score = 1 if cr_1 > cr_2 else 0

            # Score #7 - change in Share Issued
            si_score = 0 if TTM_bsheet['Share Issued'] > bsheet[years[1-len(years)]]['Share Issued'] else 1

            # Score #8 - change in Gross Margin
            gm_1 = TTM['Gross Profit'] / TTM['Total Revenue']
            gm_2 = income[years[1-len(years)]]['Gross Profit'] / income[years[1-len(years)]]['Total Revenue']
            gm_score = 1 if gm_1 > gm_2 else 0

            #Score #9 - change in Asset Turnover
            at_1 = TTM['Total Revenue'] / TTM_bsheet4['Total Assets']
            at_2 = income[years[1-len(years)]]['Total Revenue'] / bsheet[years[2-len(years)]]['Total Assets']
            at_score = 1 if at_1 > at_2 else 0

            piotroski = at_score + gm_score + si_score + cr_score + acc_score + lv_score + croa_score + roa_score + ocf_score

            #Beneish M-Score
            #Day Sales in Receivables Index
            t1 = TTM_bsheet['Receivables']/TTM['Total Revenue'] if 'Receivables' in TTM_bsheet else 0
            pre_t1 = TTM_bsheet4['Receivables']/income[years[1-len(years)]]['Total Revenue'] if 'Receivables' in TTM_bsheet4 else 0
            dsri = t1 / pre_t1 if pre_t1!= 0 else 0
            # Gross Margin Index
            t2 = TTM['Gross Profit'] / TTM['Total Revenue']
            pre_t2 = income[years[1-len(years)]]['Gross Profit'] / income[years[1-len(years)]]['Total Revenue']
            gmi = pre_t2/t2
            # Asset Quality Index
            t3 = 1 - TTM_bsheet['Current Assets'] + TTM_bsheet['Net PPE']
            pre_t3 = 1 - TTM_bsheet4['Current Assets'] + TTM_bsheet4['Net PPE']
            aqi = t3/pre_t3
            # Sales Growth Index
            t4 = TTM['Total Revenue']
            pre_t4 = income[years[1-len(years)]]['Total Revenue']
            sgi = t4/pre_t4
            # Sales, General & Administrative expense index
            t5 = TTM['Selling General And Administration']/TTM['Total Revenue']
            pre_t5 = income[years[1-len(years)]]['Selling General And Administration']/income[years[1-len(years)]]['Total Revenue']
            sgai = t5/pre_t5
            # Depreciation Index
            t6 = TTM_cfs['Depreciation Amortization Depletion']/(TTM_cfs['Depreciation Amortization Depletion']+TTM_bsheet['Net PPE']) if 'Depreciation Amortization Depletion' in TTM_cfs else 0
            pre_t6 = cfs[years[1-len(years)]]['Depreciation Amortization Depletion']/(cfs[years[1-len(years)]]['Depreciation Amortization Depletion']+TTM_bsheet4['Net PPE']) if 'Depreciation Amortization Depletion' in cfs else 0
            depi = pre_t6/t6 if t6 != 0 else 0
            # leverage Index
            t7 = (TTM_bsheet['Long Term Debt'] + TTM_bsheet['Current Liabilities'])/TTM_bsheet['Total Assets'] if 'Long Term Debt' in TTM_bsheet else 0
            pre_t7 = (TTM_bsheet4['Long Term Debt'] + TTM_bsheet4['Current Liabilities'])/TTM_bsheet4['Total Assets'] if 'Long Term Debt' in TTM_bsheet4 else 0
            lvgi = t7/pre_t7 if pre_t7 != 0 else 0
            # Total Accruals to Total Assets
            tata = (TTM['Net Income Continuous Operations']-TTM_cfs['Operating Cash Flow'])/TTM_bsheet['Total Assets']
            m = -4.84 + 0.92*dsri + 0.52*gmi + 0.404*aqi + 0.892*sgi + 0.115*depi - 0.172*sgai + 4.679*tata - 0.327*lvgi

            summary, f_score, valuation, guru = st.tabs(
                ["Summary", "F-Score", "Valuation", "Guru"])

            with summary:
                st.subheader('Candlestick Chart')
                current = datetime.today().date()
                start_date = st.date_input('Start Date', current - timedelta(days=365))
                end_date = st.date_input('End Date', current)

                dataa = yf.download(ticker, start=start_date, end=end_date)

                # Các đường trung bình
                dataa['EMA20'] = dataa['Close'].ewm(span=20, adjust=False).mean()
                dataa['MA50'] = dataa['Close'].rolling(50).mean()
                dataa['MA100'] = dataa['Close'].rolling(100).mean()
                dataa['MA150'] = dataa['Close'].rolling(150).mean()

                if dataa.empty:
                    st.write("<p style='color:red'><strong>Please reset the date to see the chart</strong></p>",
                             unsafe_allow_html=True)
                else:
                    fig = go.Figure(data=[
                        go.Candlestick(x=dataa.index, open=dataa['Open'], high=dataa['High'], low=dataa['Low'],
                                       close=dataa['Close'],
                                       name='Candle Stick'),
                        go.Scatter(x=dataa.index, y=dataa['EMA20'], line=dict(color='green', width=1.5, dash='dot'),
                                   name='EMA20'),
                        go.Scatter(x=dataa.index, y=dataa['MA50'], line=dict(color='blue', width=1.5), name='MA50'),
                        go.Scatter(x=dataa.index, y=dataa['MA100'], line=dict(color='yellow', width=1.5), name='MA100'),
                        go.Scatter(x=dataa.index, y=dataa['MA150'], line=dict(color='red', width=1.5), name='MA150'),
                    ])

                    fig.update_layout(autosize=True, width=900, height=800,
                                      legend=dict(orientation="h", yanchor="top", y=1.08, xanchor="right", x=1))

                    st.plotly_chart(fig)

                    # Lấy thông tin cơ bản (profile) của mã cổ phiếu
                    mck_info = mck.get_info()

                    # Tạo DataFrame từ thông tin cơ bản
                    df = pd.DataFrame({
                        'Tiêu đề': ['Address', 'City', 'Country', 'Website', 'Industry', 'Sector', 'Description'],
                        'Thông tin': [
                            mck_info.get('address1', 'N/A'),
                            mck_info.get('city', 'N/A'),
                            mck_info.get('country', 'N/A'),
                            mck_info.get('website', 'N/A'),
                            mck_info.get('industry', 'N/A'),
                            mck_info.get('sector', 'N/A'),
                            mck_info.get('longBusinessSummary', 'N/A')
                        ]
                    })

                    # Hiển thị bảng thông tin cơ bản
                    st.table(df)

                datav = {
                    'Time': [year.date().strftime("%Y-%m-%d") for year in years[::-1]] + ['TTM'],
                    'Revenue': [income.loc['Total Revenue', year] for year in years[::-1]] + [
                        TTM['Total Revenue']],
                    'Net Income': [income.loc['Net Income', year] for year in years[::-1]] + [
                        TTM['Net Income']],
                    'Free Cash Flow': [cfs.loc['Free Cash Flow', year] for year in years[::-1]] + [
                        TTM_cfs['Free Cash Flow']],
                    'Operating Cash Flow': [cfs.loc['Operating Cash Flow', year] for year in years[::-1]] + [
                        TTM_cfs['Operating Cash Flow']],
                    'ROE': [income.loc['Net Income', year] / (
                            bsheet.loc['Total Equity Gross Minority Interest', year] or 1)
                            for
                            year in years[::-1]] + [
                               TTM['Net Income'] / TTM_bsheet['Total Equity Gross Minority Interest']],
                    'EPS': [income.loc['Net Income', year] / (mck.info['sharesOutstanding'] or 1) for year in
                            years[::-1]] + [
                               TTM['Basic EPS']],
                    'Current Ratio': [bsheet.loc['Current Assets', year] / (
                            bsheet.loc['Current Liabilities', year] or 1)
                                      for
                                      year in years[::-1]] + [
                                         TTM_bsheet['Current Assets'] / TTM_bsheet['Current Liabilities']],
                    'Debt to Equity Ratio': [bsheet.loc['Total Debt', year] / (
                            bsheet.loc['Total Equity Gross Minority Interest', year] or 1) for year in
                                             years[::-1]] + [
                                                TTM_bsheet['Total Debt'] / TTM_bsheet[
                                                    'Total Equity Gross Minority Interest']],
                    'Accounts Receivable': [bsheet.loc['Accounts Receivable', year] for year in years[::-1]] + [
                        TTM_bsheet['Accounts Receivable']]
                }

                dfv = pd.DataFrame(datav)

                # Plot the chart using Plotly Express
                # Revenue, Net Income, Operating Cash Flow
                # create plot
                columns_to_plot = ['Revenue', 'Net Income', 'Operating Cash Flow','Free Cash Flow']
                x = ['['] + dfv['Time'] + [']']
                # Plot grouped bar chart
                fig = px.bar(dfv, x, y=columns_to_plot, title='Financial Ratios',
                            labels={'value': 'Value', 'variable': 'Legend'},
                            height=460, width=1200, barmode='group')

                # Add text on top of each bar
                for col in columns_to_plot:
                    new_values = dfv[col] / 1e9
                    fig.update_traces(text=new_values.apply(lambda x: f'{x:.2f}B'), textposition='outside', selector=dict(name=col))
                fig.update_xaxes(fixedrange=True, title_text="Time")
                # Display the chart in Streamlit app
                st.plotly_chart(fig)

                # EPS
                # Vẽ biểu đồ đường sử dụng Plotly Express
                dfv['EPS'] = dfv['EPS'].round(2)
                fig = px.line(dfv, x, y='EPS', title='EPS', markers = 'o', line_shape='spline', text='EPS')
                fig.update_traces(textposition='top center')
                fig.update_xaxes(fixedrange=True)
                fig.update_xaxes(title_text="Time")
                # Thay đổi màu của đường
                fig.update_traces(line=dict(color='firebrick'))
                # Hiển thị biểu đồ trong ứng dụng Streamlit
                st.plotly_chart(fig)

                # ROE
                # Vẽ biểu đồ đường sử dụng Plotly Express
                dfv['ROE'] = dfv['ROE'].round(2)
                fig = px.line(dfv, x, y='ROE', title='ROE', markers = 'o', line_shape='spline', text='ROE')
                fig.update_traces(textposition='top center')
                fig.update_xaxes(fixedrange=True)
                fig.update_xaxes(title_text="Time")
                # Thay đổi màu của đường
                fig.update_traces(line=dict(color='mediumspringgreen'))
                # Hiển thị biểu đồ trong ứng dụng Streamlit
                st.plotly_chart(fig)

                # Debt to Equity Ratio
                # Vẽ biểu đồ đường sử dụng Plotly Express
                dfv['Debt to Equity Ratio'] = dfv['Debt to Equity Ratio'].round(2)
                fig = px.line(dfv, x, y='Debt to Equity Ratio', title='Debt to Equity Ratio', markers = 'o', line_shape='spline', text='Debt to Equity Ratio')
                fig.update_traces(textposition='top center')
                fig.update_xaxes(fixedrange=True)
                fig.update_xaxes(title_text="Time")
                # Thay đổi màu của đường
                fig.update_traces(line=dict(color='dodgerblue'))
                # Hiển thị biểu đồ trong ứng dụng Streamlit
                st.plotly_chart(fig)

                # Current Ratio
                # Vẽ biểu đồ đường sử dụng Plotly Express
                dfv['Current Ratio'] = dfv['Current Ratio'].round(2)
                fig = px.line(dfv, x, y='Current Ratio', title='Current Ratio', markers = 'o', line_shape='spline', text='Current Ratio')
                fig.update_traces(textposition='top center')
                fig.update_xaxes(fixedrange=True)
                # Thay đổi các chú thích trên trục x
                fig.update_xaxes(title_text="Time")
                # Thay đổi màu của đường
                fig.update_traces(line=dict(color='rosybrown'))
                # Hiển thị biểu đồ trong ứng dụng Streamlit
                st.plotly_chart(fig)

            with f_score:
                st.subheader('F-Score')
                data00 = [
                    ('Time', *[year.date().strftime("%Y-%m-%d") for year in years[::-1]], 'TTM', 'Total'),
                    ('Revenue', '-', *[rv_scores[i] for i in range(len(rv_scores))], str(TTM_rv_score),
                     str(total_rv_score) + ' / ' + str(len(rv_scores) + 1)),
                    ('Net Income', '-', *[ni_scores[i] for i in range(len(ni_scores))], str(TTM_ni_score),
                     str(total_ni_score) + ' / ' + str(len(ni_scores) + 1)),
                    ('Operating Cash Flow', '-', *[opcf_scores[i] for i in range(len(opcf_scores))], str(TTM_opcf_score),
                     str(total_opcf_score) + ' / ' + str(len(opcf_scores) + 1)),
                    ('Free Cash Flow', '-', *[fcf_scores[i] for i in range(len(fcf_scores))], str(TTM_fcf_score),
                     str(total_fcf_score) + ' / ' + str(len(fcf_scores) + 1)),
                    ('EPS', '-', *[eps_scores[i] for i in range(len(eps_scores))], str(TTM_eps_score),
                     str(total_eps_score) + ' / ' + str(len(eps_scores) + 1)),
                    ('ROE', '-', *[roe_scores[i] for i in range(len(roe_scores))], str(TTM_roe_score),
                     str(total_roe_score) + ' / ' + str(len(roe_scores) + 1)),
                    ('Current Ratio', '-', *[cr_scores[i] for i in range(len(cr_scores))], str(TTM_cr_score),
                     str(total_cr_score) + ' / ' + str(len(cr_scores) + 1)),
                    ('Debt to Equity Ratio', '-', *[der_scores[i] for i in range(len(der_scores))], str(TTM_der_score),
                     str(total_der_score) + ' / ' + str(len(der_scores) + 1)),
                    ('Accounts Receivable', '-', *[ar_scores[i] for i in range(len(ar_scores))], str(TTM_ar_score),
                     str(total_ar_score) + ' / ' + str(len(ar_scores) + 1)),
                ]

                df00 = pd.DataFrame(data00[1:], columns=data00[0])
                pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))
                st.write(df00)

                st.subheader('Total F-Score = ' + str(total_score) + ' / ' + str((len(rv_scores) + 1) * 9))

                percentage = (total_score / ((len(rv_scores) + 1) * 9)) * 100
                st.subheader('Percentage = {:.2f} %'.format(percentage))

            with valuation:

                # Current year
                current_year = datetime.now().year
                st.subheader("Current Year")
                number0 = st.number_input("Current Year:", value=current_year, placeholder="Type a number...")

                # beta
                beta_value = mck.info['beta']
                st.subheader("Company Beta")
                number1 = st.number_input("Company Beta:", value=beta_value, placeholder="Type a number...")

                # fcf
                display_options = ["Free Cash Flow", "Net Income", "Operating Cash Flow"]
                selected_display_option = st.radio("Select display option:", display_options)

                if selected_display_option == "Free Cash Flow":
                    free_cash_flow = TTM_cfs['Free Cash Flow']
                    formatted_free_cash_flow = "{:,.2f}".format(free_cash_flow)
                    number2_str = st.text_input("Free Cash Flow (current):", value=formatted_free_cash_flow,
                                                placeholder="Type a number...")
                    number2 = float(number2_str.replace(',', ''))


                elif selected_display_option == "Net Income":
                    net_income = TTM['Net Income']
                    formatted_net_income = "{:,.2f}".format(net_income)
                    number2_str = st.text_input("Net Income:", value=formatted_net_income, placeholder="Type a number...")
                    number2 = float(number2_str.replace(',', ''))

                elif selected_display_option == "Operating Cash Flow":
                    operating_cash_flow = TTM_cfs['Operating Cash Flow']
                    formatted_operating_cash_flow = "{:,.2f}".format(operating_cash_flow)
                    number2_str = st.text_input("Operating Cash Flow:", value=formatted_operating_cash_flow,
                                                placeholder="Type a number...")
                    number2 = float(number2_str.replace(',', ''))

                # debt
                ttm_cr = TTM_bsheet['Current Debt'] if 'Current Debt' in TTM_bsheet else TTM_bsheet[
                    'Current Capital Lease Obligation'] if 'Current Capital Lease Obligation' in TTM_bsheet else 0
                st.subheader("Current Debt")
                formatted_ttm_cr = "{:,.2f}".format(ttm_cr)
                number5_str = st.text_input("Current Debt:", value=formatted_ttm_cr, placeholder="Type a number...")
                number5 = float(number5_str.replace(',', ''))

                # cash
                cash = TTM_bsheet.loc['Cash Cash Equivalents And Short Term Investments']
                st.subheader("Cash and Short Term Investments:")
                formatted_cash = "{:,.2f}".format(cash)
                number6_str = st.text_input("Cash and Short Term Investments:", value=formatted_cash,
                                            placeholder="Type a number...")
                number6 = float(number6_str.replace(',', ''))

                # shares
                shares_outstanding = mck.info['sharesOutstanding']
                st.subheader("Shares Outstanding:")
                formatted_shares_outstanding = "{:,.2f}".format(shares_outstanding)
                number7_str = st.text_input("Shares Outstanding:", value=formatted_shares_outstanding,
                                            placeholder="Type a number...")
                number7 = float(number7_str.replace(',', ''))


                # Tính toán discount rate dựa trên giá trị beta

                def calculate_discount_rate(beta):
                    if number1 < 1.00:
                        return 0.05
                    elif 1.00 <= number1 < 1.1:
                        return 0.06
                    elif 1.1 <= number1 < 1.2:
                        return 0.065
                    elif 1.2 <= number1 < 1.3:
                        return 0.07
                    elif 1.3 <= number1 < 1.4:
                        return 0.075
                    elif 1.4 <= number1 < 1.5:
                        return 0.08
                    elif 1.5 <= number1 < 1.6:
                        return 0.085
                    elif number1 >= 1.6:
                        return 0.09


                # Tính toán discount rate tương ứng
                discount_rate_value = calculate_discount_rate(beta_value)
                formatted_discount_rate_value = "{:,.3f}".format(discount_rate_value)

                # Nhập growth rate
                st.subheader("Growth Rate")
                growth_rate1_str = st.text_input('Growth rate Y1-5', value="%")
                if growth_rate1_str.strip() == "%":  # Kiểm tra nếu chuỗi chỉ là ký tự '%'
                    growth_rate1 = 0.0  # Gán giá trị mặc định cho trường hợp này
                else:
                    growth_rate1 = float(growth_rate1_str.replace(',', '').replace('%', '')) / 100

                growth_rate2_str = st.text_input('Growth rate Y6-10', value="%")
                if growth_rate2_str.strip() == "%":  # Kiểm tra nếu chuỗi chỉ là ký tự '%'
                    growth_rate2 = 0.0  # Gán giá trị mặc định cho trường hợp này
                else:
                    growth_rate2 = float(growth_rate2_str.replace(',', '').replace('%', '')) / 100

                growth_rate3_str = st.text_input('Growth rate Y11-20', value="%")
                if growth_rate3_str.strip() == "%":  # Kiểm tra nếu chuỗi chỉ là ký tự '%'
                    growth_rate3 = 0.0  # Gán giá trị mặc định cho trường hợp này
                else:
                    growth_rate3 = float(growth_rate3_str.replace(',', '').replace('%', '')) / 100

                # Hiển thị discount rate trên Streamlit
                st.subheader(" Discount Rate")
                number8_str = st.text_input('Discount Rate: ', value=formatted_discount_rate_value,
                                            placeholder="Type a number...")
                number8 = float(number8_str.replace(',', '').replace(' %', ''))
                # Creating the first table
                data1 = {
                    'Operating Cash Flow/Free Cash Flow/Net Income': [number2],
                    'Growth rate (Y 1-5)': growth_rate1,
                    'Growth rate (Y 6-10)': growth_rate2,
                    'Growth rate (Y 11-20)': growth_rate3,
                    'Discount rate': number8,
                    'Current year': number0
                }

                table1 = pd.DataFrame(data=data1)

                # Creating the second table with calculations based on the first table
                years = [
                    ((table1['Current year'][0]) + i)
                    for i in range(21)
                ]
                cash_flows = [
                    (table1['Operating Cash Flow/Free Cash Flow/Net Income'][0] * (
                                (1 + table1['Growth rate (Y 1-5)'][0]) ** i)) if i <= 5
                    else ((table1['Operating Cash Flow/Free Cash Flow/Net Income'][0] * (
                                (1 + table1['Growth rate (Y 1-5)'][0]) ** 5)) * (
                                  (1 + table1['Growth rate (Y 6-10)'][0]) ** (i - 5))) if 6 <= i <= 10
                    else ((table1['Operating Cash Flow/Free Cash Flow/Net Income'][0] * (
                                (1 + table1['Growth rate (Y 1-5)'][0]) ** 5)) * (
                                  (1 + table1['Growth rate (Y 6-10)'][0]) ** 5) * (
                                  (1 + table1['Growth rate (Y 11-20)'][0]) ** (i - 10)))
                    for i in range(21)
                ]

                discount_factors = [(1 / ((1 + table1['Discount rate'][0]) ** i)) for i in range(21)]
                discounted_values = [cf * df for cf, df in zip(cash_flows, discount_factors)]

                data2 = {
                    'Year': years[1:],
                    'Cash Flow': cash_flows[1:],
                    'Discount Factor': discount_factors[1:],
                    'Discounted Value': discounted_values[1:]
                }

                table2 = pd.DataFrame(data=data2)
                pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))
                table2['Year'] = table2['Year'].astype(str).str.replace(',', '')
                st.subheader('Discounted Cash Flow')
                st.write(table2)

                # Chart
                cash_flow = table2['Cash Flow']
                discounted_value = table2['Discounted Value']
                years = table2['Year']
                columns_to_plot = ['Cash Flow', 'Discounted Value']
                fig = px.line(table2, x=years, y=columns_to_plot,
                              title='Intrinsic Value Calculator (Discounted Cash Flow Method 10 years)',
                              labels={'value': 'Value', 'variable': 'Legend'},
                              height=500, width=800, markers='o')
                fig.update_xaxes(fixedrange=True)

                # Thay đổi các chú thích trên trục x
                fig.update_xaxes(
                    tickvals=years[0:]
                )
                fig.update_xaxes(title_text="Time")
                st.plotly_chart(fig)

                # Tính Intrinsic Value
                total_discounted_value = sum(discounted_values)
                st.write(f"PV of 20 yr Cash Flows: {total_discounted_value:,.2f}")

                intrinsic_value = sum(discounted_values) / number7
                st.write(f"Intrinsic Value before cash/debt: {intrinsic_value:,.2f}")

                debt_per_share = number5 / number7
                st.write(f"Debt per Share: {debt_per_share:,.2f}")

                cash_per_share = number6 / number7
                formatted_cash_per_share = '{:,.2f}'.format(cash_per_share)
                st.write(f"Cash per Share: {formatted_cash_per_share}")

                final_intrinsic_value = intrinsic_value - debt_per_share + cash_per_share
                st.subheader(f"Final Intrinsic Value per Share: {final_intrinsic_value:,.2f}")

            with guru:

                st.subheader('Liquidity Ratio')
                data_liquidity = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4, 5, 6],
                        "Index": ['Current Ratio', 'Quick Ratio', 'Cash Ratio', 'Days Inventory', 'Days Sales Outstanding',
                                  'Days Payable'],
                        "Current": [cr_ratio, qr_ratio, car_ratio, dio_ratio, dso_ratio, dp_ratio],
                        "Vs History": [cr_values2, qr_values, car_values, dio_values, dso_values, dp_values],
                    }
                )
                st.data_editor(
                    data_liquidity,
                    column_config={
                        "Vs History": st.column_config.ProgressColumn(
                            "Vs History",
                        ),
                    },
                    hide_index=True,
                )

                st.subheader('Dividend & Buy Back')
                data_dividend = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4],
                        "Index": ['Dividend Yield', 'Dividend Payout Ratio', '5-Year Yield-on-Cost',
                                  'Forward Dividend Yield'],
                        "Current": [div_ratio, pr_ratio, five_years_ratio, forward_ratio],
                        "Vs History": [div_values, pr_values, five_years_values, forward_values],
                    }
                )
                st.data_editor(
                    data_dividend,
                    column_config={
                        "Vs History": st.column_config.ProgressColumn(
                            "Vs History",
                        ),
                    },
                    hide_index=True,
                )

                st.subheader('Profitability Rank')
                data_profitability = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4, 5, 6, 7, 8],
                        "Index": ['	Gross Margin %', '	Operating Margin %', '	Net Margin %', '	FCF Margin %',
                                  '	ROE %',
                                  '	ROA %', '	ROC (Joel Greenblatt) %', '	ROCE %'],
                        "Current": [gr_margin, op_margin, net_margin, fcf_margin, roe_margin, roa_margin, roc_margin,
                                    roce_margin],
                        "Vs History": [gr_values, op_values, net_values, fcf_ma_values, roe_ma_values, roa_values,
                                       roc_values, roce_values],
                    }
                )
                st.data_editor(
                    data_profitability,
                    column_config={
                        "Vs History": st.column_config.ProgressColumn(
                            "Vs History",
                        ),
                    },
                    hide_index=True,
                )
                st.subheader('GF Values')
                data_GF_Value = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                        "Index": ['PE Ratio', 'PS Ratio', 'PB Ratio', 'Price-to-tangible-book Ratio',
                                  'Price-to-Free-Cash_Flow Ratio',
                                  'EV-to-EBIT', 'EV-to-EBITDA', 'EV-to-Revenue', 'EV-to-FCF',
                                  'Price-to-Net-Current-Asset-Value', 'Earnings Yields (Greenblatt) %', 'FCF Yield %'],
                        "Current": [PE_ratio, PS_ratio, PB_ratio, Price_to_TBV, price_to_FCF, EV_to_EBIT, EV_to_EBITDA,
                                    EV_to_Revenue, EV_to_FCF, Price_to_Net_CAV, EarningsYields, FCFYield],
                        "Vs History": [PE_ratio2, PS_ratio2, PB_ratio2, Price_to_TBV2, price_to_FCF2, EV_to_EBIT2,
                                       EV_to_EBITDA2, EV_to_Revenue2, EV_to_FCF2, Price_to_Net_CAV2, EarningsYields2,
                                       FCFYield2],
                    }
                )
                st.data_editor(
                    data_GF_Value,
                    column_config={
                        "Vs History": st.column_config.ProgressColumn(
                            "Vs History",
                        ),
                    },
                    hide_index=True,
                )

                st.subheader('Financial Strength')
                #WACC vs ROIC
                risk_free = st.number_input("Risk Free Rate:", placeholder="Type a number...")
                average_market_risk = st.number_input("Average Market Risk:", placeholder="Type a number...")
                capm = risk_free + mck.info['beta']*average_market_risk #cost of equity
                ave_debt = TTM_bsheet3/4
                cost_of_debt = TTM['Interest Expense']/ave_debt['Total Debt']
                tax_rate = TTM['Tax Provision']/TTM['Pretax Income']
                market_cap = mck.info['marketCap'] if 'marketCap' in mck.info else mck.basic_info['marketCap']
                wacc = (market_cap/(market_cap+ave_debt['Total Debt'])) * capm + (ave_debt['Total Debt']/(market_cap+ave_debt['Total Debt'])) * cost_of_debt *(1-tax_rate)

                #roic
                invest_cap_dec = TTM_bsheet['Total Assets'] - TTM_bsheet['Payables And Accrued Expenses'] - (TTM_bsheet['Cash Cash Equivalents And Short Term Investments']
                                - max(0,(TTM_bsheet['Current Liabilities'] - TTM_bsheet['Current Assets'] + TTM_bsheet['Cash Cash Equivalents And Short Term Investments']))) if 'Payables And Accrued Expenses' in TTM_bsheet else 0
                invest_cap_sep = TTM_bsheet2['Total Assets'] - TTM_bsheet2['Payables And Accrued Expenses'] - (TTM_bsheet2['Cash Cash Equivalents And Short Term Investments']
                                - max(0,(TTM_bsheet2['Current Liabilities'] - TTM_bsheet2['Current Assets'] + TTM_bsheet2['Cash Cash Equivalents And Short Term Investments']))) if 'Payables And Accrued Expenses' in TTM_bsheet2 else 0
                roic = TTM['Operating Income'] * (1-tax_rate) / (1/2 * (invest_cap_dec + invest_cap_sep)) if (1/2 * (invest_cap_dec + invest_cap_sep)) !=0 else 0

                wacc_roic = wacc/roic if roic !=0 else None
                data_financial = pd.DataFrame(
                    {
                        "STT": [1, 2, 3, 4, 5],
                        "Index": ['Cash to Debt', 'Equity to Assets', 'Debt to Equity', 'Debt to EBITDA', 'Interest Coverage'],
                        "Current": [cash_debt, equity_asset, debt_equity, debt_ebitda, interest_coverage],
                        "Vs History": [cash_debt_values, equity_asset_values, debt_equity_values, debt_ebitda_values, interest_coverage_values],
                    }
                )
                st.data_editor(
                    data_financial,
                    column_config={
                        "Vs History": st.column_config.ProgressColumn(
                            "Vs History",
                        ),
                    },
                    hide_index=True,
                )

                st.subheader('Score')
                data_score = pd.DataFrame(
                    {
                        "Index": ['WACC vs ROIC', 'Altman Z-Score', 'Beneish M-Score', 'Piotroski F-Score'],
                        "Value": [wacc_roic, altmanz_score, m, piotroski],
                    }
                )
                st.write(data_score)

except KeyError:
    st.caption('Thông tin không đầy đủ để đánh giá')