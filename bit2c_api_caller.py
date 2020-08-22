import requests
import time
import ccxt
import matplotlib.pyplot as plt

PAIRS           = ['BtcNis', 'EthNis', 'BchabcNis', 'LtcNis', 'EtcNis', 'BtgNis', 'BchsvNis', 'GrinNis']
PAIRS_FOR_TRADE = [True,     True,     False,       False,    False,    False,    False,      False]

NORMAL               = 0
BUY_ONLY             = 1
CANCEL_ALL           = 2
BUY_SELL_AT_DISCOUNT = 3

# Normal Mode:
# EXISTING_INDICATOR_PERCENT = 3.0
# COMMISSION_PERCENT = 1.0
# COMMISSION_FACTOR = 10.0
# COMMISSION_PERCENT_THRESHOLD = round(float(COMMISSION_PERCENT*COMMISSION_FACTOR), 4)
# BUY_ABOVE_COMMISSION = round(float(1)+float(COMMISSION_PERCENT)/100, 4)
# SELL_BELOW_COMMISSION = round(float(1)-float(COMMISSION_PERCENT)/100, 4)
# ORDER_PERCENTAGE = 2.5  # percentage of balance to spend on recommended order
# MINIMUM_ORDER_NIS = 45.0
# NUM_ITERATIONS_AFTER_WHICH_TO_CHECK_SANITY = 5  # After 6 iterations, if there is no change in number of requried orders, then the quota of open orders was likely to have been reached
# SPREAD_ADVANCE_FACTOR = 1.0 # COMMISSION_FACTOR / (2*NUM_ITERATIONS_AFTER_WHICH_TO_CHECK_SANITY)
# RUN_ONCE = False
# CANCEL_ALL_ORDERS = False


# BUY-only mode:
# MODE = BUY_ONLY
EXISTING_INDICATOR_PERCENT = 3.0
COMMISSION_PERCENT = 1.0
COMMISSION_FACTOR = 10.0
COMMISSION_PERCENT_THRESHOLD = round(float(COMMISSION_PERCENT*COMMISSION_FACTOR), 4)
BUY_ABOVE_COMMISSION = round(float(1)+float(COMMISSION_PERCENT)/100, 4)
SELL_BELOW_COMMISSION = round(float(1)-float(COMMISSION_PERCENT)/100, 4)
ORDER_PERCENTAGE = 2.5  # percentage of balance to spend on recommended order
MINIMUM_ORDER_NIS = 250.0
NUM_ITERATIONS_AFTER_WHICH_TO_CHECK_SANITY = 6  # After 6 iterations, if there is no change in number of requried orders, then the quota of open orders was likely to have been reached
SPREAD_ADVANCE_FACTOR = 0.0 # COMMISSION_FACTOR / (2*NUM_ITERATIONS_AFTER_WHICH_TO_CHECK_SANITY)
RUN_ONCE = True
CANCEL_ALL_ORDERS = False

# Place Buys at 10% OFF and Sells and 10% over:
MODE = BUY_SELL_AT_DISCOUNT
GRAPH_ONLY = True
GRAPH_PERIOD_SEC = 600
INFORMATIVE_ONLY = True
ORDER_PERCENTAGE = 10.0
DISCOUNT_BUY_PERCENTAGE = 10.0

# Cancell All orders:
# MODE = CANCEL_ALL
# CANCEL_ALL_ORDERS = True
# RUN_ONCE = True


def bit2c_classic_margins(endless_mode):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/61.0.3163.79 '
                             'Safari/537.36'}  # 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'}
    session = requests.Session()
    session.headers.update(headers)

    while True:
        spread_orders = {}
        print("\n\n[bit2c_classic_margins] Recommendations:\n=========================================")
        for pair in PAIRS:
            url = 'https://bit2c.co.il/Exchanges/{}/orderbook.json'.format(pair)
            try:
                r = session.get(url)  # common.DEFAULT_HEADERS)
                r.raise_for_status()
                data = r.json()
            except:
                print("[bit2c_classic_margins] Exception: Failed to Connect to url {}".format(url))
                return

            if len(data["bids"]) is 0 or len(data["asks"]) is 0:
                continue

            if PAIRS_FOR_TRADE[PAIRS.index(pair)] is False:
                continue

            highest_bid = data["bids"][0][0]
            lowest_ask  = data["asks"][0][0]
            spread = round(100*(float(lowest_ask)-float(highest_bid))/float(lowest_ask),4)
            adapted_pair = pair.replace('Nis', '/Nis').upper().replace('BCHABC', 'BCH').replace('BCHSV', 'BSV')

            if MODE == BUY_SELL_AT_DISCOUNT:
                spread_orders[adapted_pair] = {
                        'buy' : {
                                'at': highest_bid*(1-DISCOUNT_BUY_PERCENTAGE/100)
                        },
                        'sell': {
                                'at': lowest_ask*(1+DISCOUNT_BUY_PERCENTAGE/100)
                        }
                }
            else:
                if spread > COMMISSION_PERCENT_THRESHOLD:
                    # print("{:10}: [bid, ask] = [{:10}, {:10}], spread[%]={:10}".format(pair, highest_bid, lowest_ask, spread))
                    buy_at  = round(highest_bid*BUY_ABOVE_COMMISSION,  2)
                    sell_at = round(lowest_ask *SELL_BELOW_COMMISSION, 2)
                    print("     SELL {:10} at {:10}".format(pair.replace('Nis', '').upper(), sell_at))
                    print("     BUY  {:10} at {:10}".format(pair.replace('Nis', '').upper(), buy_at))
                    print("    ===============================")
                    spread_orders[adapted_pair] = {
                            'buy': {
                                    'at': buy_at
                            },
                            'sell': {
                                    'at': sell_at
                            }
                    }

        if not endless_mode:
            return spread_orders
        time.sleep(1)


API_1 = {
        'key': 'key-here',
        'secret': 'SECRET-HERE'
}


def connect_to_bit2c(plot, api, balances):
    # from variable id
    exchange_id = 'bit2c'
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
            'apiKey'         : api["key"].upper(),
            'secret'         : api["secret"],
            'timeout'        : 30000,
            'enableRateLimit': True,
    })
    print('[connect_to_bit2c] Fetching Balances...')
    balances['data'] = exchange.fetch_balance()
    print('[connect_to_bit2c] Balances: {}'.format(balances))
    labels = []
    sizes = []
    explodes = []
    total_nis = 0
    for item, value in balances['data']['info'].items():
        if 'ESTIMATED_BALANCE_' in item:
            item_name = item.replace('ESTIMATED_BALANCE_', '').replace('_IN_NIS', '') + ' = {} NIS'.format(int(round(value,0)))
            print('    {} = {}'.format(item_name, value))
            labels.append(item_name)
            sizes.append(value)
            explodes.append(0)
            total_nis += value;
    if plot:
        plt.clf()
        plt.pie(sizes, labels=labels, explode=explodes, autopct='%1.1f%%', shadow=True, startangle=180)
        plt.axis('equal')
        plt.show(block=False)
        plt.title('Total value: {} NIS'.format(int(round(total_nis,0))))
        plt.pause(GRAPH_PERIOD_SEC)
        plt.close

    return exchange


def cancel_my_open_orders(exchange, markets):
    my_open_orders = {}
    for market in markets:
        open_orders = exchange.fetch_open_orders(market)
        print('[cancel_my_open_orders] {} orders are {}'.format(market, open_orders))
        if len(open_orders):
            for order in open_orders:
                print('    Cancelling [{:4} {:6} {:9} at {:5}]'.format(order['side'], order['amount'], order['symbol'], order['price']))
                exchange.cancel_order(order['id'])


def scan_my_open_orders(exchange, markets, return_only_edges=True):
    my_open_orders = {}
    for market in markets:
        print('Market: {}'.format(market))
        adapted_market = market.replace('BTC', 'Btc').replace('ETH', 'Eth').replace('BCH', 'Bchabc').replace('LTC', 'Ltc').replace('ETC', 'Etc').replace('BTG', 'Btg').replace('BSV', 'Bchsv').replace('GRIN', 'Grin').replace('/NIS', 'Nis')
        print('adapted_market: {}'.format(adapted_market))
        print('PAIRS.index(adapted_market): {}'.format(PAIRS.index(adapted_market)))

        if PAIRS_FOR_TRADE[PAIRS.index(adapted_market)] is False:
            continue
        open_orders = exchange.fetch_open_orders(market)
        print('[scan_my_open_orders] Scanning {} open {} orders'.format(len(open_orders), market))
        if len(open_orders):
            my_lowest_sell = None
            my_highest_buy = None
            my_open_orders_for_this_market = []
            for order in open_orders:
                my_order = {
                        'side'  : order['side'],
                        'amount': order['amount'],
                        'price' : order['price']
                }
                if return_only_edges:
                    if order['side'] == 'sell':
                        if my_lowest_sell is None:
                            my_lowest_sell = my_order
                        elif my_order['price'] < my_lowest_sell['price']:
                            my_lowest_sell = my_order
                    elif order['side'] == 'buy':
                        if my_highest_buy is None:
                            my_highest_buy = my_order
                        elif my_order['price'] > my_highest_buy['price']:
                            my_highest_buy = my_order
                else:
                    my_open_orders_for_this_market.append(my_order)
            if return_only_edges:
                if my_lowest_sell is not None:
                    my_open_orders_for_this_market.append(my_lowest_sell)
                if my_highest_buy is not None:
                    my_open_orders_for_this_market.append(my_highest_buy)
            my_open_orders[market] = my_open_orders_for_this_market

    return my_open_orders


# The spread_pair is the recommended buy/sell. If an open order exists, and within an EXISTING_INDICATOR_PERCENT from it,
# then the recommended spread is not required
def get_required_orders(spread_orders, my_open_orders, allow_multiple_spread_orders, factor):  # factor is percentage to spread when my order already exists
    required_orders = []

    for spread_pair, spread_order in spread_orders.items():
        print('\n\n[get_required_orders] {}: spread_order = {}, factor = {}'.format(spread_pair, spread_order, factor))
        print('=========================================================================================================')
        # Need to normalize the sell/buy to yield the same NIS value:
        # Consider: Sell at 40, buy at 15. So normalize sell *AMOUNT* by 15/40
        if spread_pair in list(my_open_orders.keys()):
            print("[get_required_orders] {} exists in list(my open orders.keys())".format(spread_pair))
            added_sell = False
            added_buy  = False
            for my_open_order in my_open_orders[spread_pair]:
                print("[get_required_orders] Checking my_open_order: {}".format(my_open_order))
                if not added_sell and my_open_order['side'] == 'sell' and (abs(my_open_order['price']-spread_order['sell']['at'])/my_open_order['price'] > EXISTING_INDICATOR_PERCENT/100 or allow_multiple_spread_orders):
                    added_sell = True
                    if MODE != BUY_ONLY:
                        order = {
                                'pair': spread_pair,
                                'side': 'sell',
                                'price': round(spread_order['sell']['at']*(1.0 - float(factor)/100),4),
                                'normalization_factor': spread_order['buy']['at']/spread_order['sell']['at']
                        }
                        print('[get_required_orders] Adding Recommended order: {}'.format(order))
                        required_orders.append(order)
                if not added_buy and my_open_order['side'] == 'buy' and (abs(my_open_order['price']-spread_order['buy']['at'])/my_open_order['price'] > EXISTING_INDICATOR_PERCENT/100 or allow_multiple_spread_orders):
                    added_buy = True
                    order = {
                            'pair': spread_pair,
                            'side': 'buy',
                            'price': round(spread_order['buy']['at']*(1.0 + float(factor)/100),4),
                            'normalization_factor': 1.0
                    }
                    print('[get_required_orders] Adding Recommended order: {}'.format(order))
                    required_orders.append(order)
        else:
            print("[get_required_orders] spread pair {} does not exist in my open orders".format(spread_pair))
            print('[get_required_orders] Recommended order: {} {}'.format(spread_pair, spread_order))
            if MODE != BUY_ONLY:
                order_sell = {
                        'pair' : spread_pair,
                        'side' : 'sell',
                        'price': spread_order['sell']['at'],
                        'normalization_factor': spread_order['buy']['at']/spread_order['sell']['at']
                }
                required_orders.append(order_sell)
            order_buy  = {
                    'pair' : spread_pair,
                    'side' : 'buy',
                    'price': spread_order['buy']['at'],
                    'normalization_factor': 1.0
            }
            required_orders.append(order_buy)
    return required_orders


def create_priced_orders(required_orders, balances):
    priced_orders = []
    print('\n[create_priced_orders] balances = {}'.format(balances))
    for required_order in required_orders:
        currency = required_order['pair'].replace('/NIS', '')
        available_str = 'AVAILABLE_' + currency.replace('BCH','BCHABC').replace('BSV', 'BCHSV')
        print('[create_priced_orders] currency = {}, available_str = {}, balance = {}'.format(currency, available_str, round(balances['data']['info'][available_str],2)))
        print('[create_priced_orders] required_order: {}'.format(required_order))
        if required_order['side'] == 'sell' and balances['data']['info'][available_str] > 0:
            amount = round(balances['data']['info'][available_str]*ORDER_PERCENTAGE/100,2)*required_order['normalization_factor']
            if amount*required_order['price'] < MINIMUM_ORDER_NIS:
                amount = round(MINIMUM_ORDER_NIS/required_order['price'],2)
            priced_order = {
                'pair': required_order['pair'],
                'side': 'sell',
                'amount': amount,
                'price': required_order['price']
            }
            print('[create_priced_orders] Adding priced_order: {}'.format(priced_order))
            priced_orders.append(priced_order)
        elif required_order['side'] == 'buy' and balances['data']['info'][available_str] > 0:
            amount = round(balances['data']['info'][available_str]*ORDER_PERCENTAGE/100,2)*required_order['normalization_factor']
            if amount*required_order['price'] < MINIMUM_ORDER_NIS:
                amount = round(MINIMUM_ORDER_NIS/required_order['price'],2)
            priced_order = {
                'pair': required_order['pair'],
                'side': 'buy',
                'amount': amount,
                'price': required_order['price']
            }
            print('[create_priced_orders] Adding priced_order: {}'.format(priced_order))
            priced_orders.append(priced_order)
    return priced_orders


def execute_priced_orders(exchange, priced_orders):
    for order in priced_orders:
        print('[execute_priced_orders] placing order {}'.format(order))
        try:
            if order['side'] == 'sell':
                exchange.create_limit_sell_order(order['pair'], order['amount'], order['price'])
            elif order['side'] == 'buy':
                exchange.create_limit_buy_order(order['pair'], order['amount'], order['price'])
        except:
            print('[execute_priced_orders] FAILED placing order {}'.format(order))


def main():
    iteration = 0
    num_of_my_previous_required_orders = 0
    while True:
        iteration += 1

        balances = {}
        exchange = connect_to_bit2c(plot=GRAPH_ONLY, api=API_1, balances=balances)  # False/True for debug Plot
        if GRAPH_ONLY:
            if RUN_ONCE:
                return
            else:
                continue
        markets = exchange.load_markets()

        if iteration == 1 and CANCEL_ALL_ORDERS:
            cancel_my_open_orders(exchange, markets)
            if MODE == CANCEL_ALL:
                return
            print('[main] Sleep a little to let the other traders calm down')
            time.sleep(5)  # Sleep a little to let the other traders calm down

        spread_orders = bit2c_classic_margins(endless_mode=False)

        my_open_orders = scan_my_open_orders(exchange, markets)
        num_of_my_open_orders = 0
        for market in my_open_orders:
            print('\n   [main] My {} Open Orders:'.format(market))
            for order in my_open_orders[market]:
                num_of_my_open_orders += 1
                print('      [main] {:5} {:11} at {:7} (Total of {})'.format(order['side'], order['amount'], order['price'], num_of_my_open_orders))

        required_orders = get_required_orders(spread_orders=spread_orders, my_open_orders=my_open_orders, allow_multiple_spread_orders=True, factor=(iteration-1)*SPREAD_ADVANCE_FACTOR)

        if iteration > NUM_ITERATIONS_AFTER_WHICH_TO_CHECK_SANITY:
            if len(required_orders) == num_of_my_previous_required_orders:
                print('[main] No change in len(required_orders)={} from last iteration, stopping run'.format(len(required_orders)))  # TODO: ASFAR: Can reset iteration to 0 for instance instead of exiting
                return

        num_of_my_previous_required_orders = len(required_orders)

        priced_orders = create_priced_orders(required_orders, balances)

        if (INFORMATIVE_ONLY):
            return

        execute_priced_orders(exchange, priced_orders)
        print('[main] Completed iteration {}'.format(iteration))
        if RUN_ONCE:
            return
        time.sleep(1)


if __name__ == '__main__':
    main()
