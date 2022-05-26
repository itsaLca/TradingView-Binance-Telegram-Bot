from db_functions import Database
from binance_functions import Binance
from telegram.ext import *
import threading, config, requests, csv, os, telebot
from message_filter_functions import *
'''This is the complete Telegram bot. Trading functions are not included here'''

class MainBot(object):
    def __init__(self):
        self.client = Binance(config.SPOTTEST_API_KEY, config.SPOTTEST_SECRET_KEY)
        self.chat_ids = None #will be assigned via message
        self.user_name_recorded = False
        self.ticker_link = 'https://api.binance.com/api/v3/ticker/price?symbol=' #need to add symbol to the end
        self.general_error_message = "Incorrect syntax or symbol. Please see example below or see /help \n\n" # Add onto the end of this message the specific command syntax needed
        self.csv_file_name = None #this will automatically delete any csv file called on /orderhistory
        self.block_tradingview = False #if True, TradingView orders will be blocked

        # ---- Initializing Functions --- #
        self.bot = telebot.TeleBot(config.TELEGRAM_BOT_KEY)
        self.updater = Updater(config.TELEGRAM_BOT_KEY, use_context=True)
        self.dp = self.updater.dispatcher
        #self.all_bot_actions()
        self.polling_thread = threading.Thread(target=self.all_bot_actions) #The bot will be polling for messages asynchronously as the rest of the app runs
        self.polling_thread.start()
        self.db = Database()
        self.chat_ids = self.db.chat_ids()

    def correct_user(self, message):
        ''' Check if correct user '''
        username = message.from_user.first_name
        chat_id = message.chat.id
        allow = self.db.user_check(chat_id,username)
        if not allow and self.user_name_recorded == False:
            self.db.save_chat(chat_id,username,True)
            self.chat_ids = self.db.chat_ids()
            self.user_name_recorded = True
            return True
        elif allow:
            return True
        else:
            self.db.save_chat(chat_id,username,False)
            message.reply_text("access denied")
            print( "incorrect user. username = "+ username + " self.user_name_recorded "+str( self.user_name_recorded))
            return False

    def error_message(self, symbol, quantity, message_type):
        if message_type == "Denied":
            self.message("A Binance order for " + str(quantity) + " " + symbol + " has been denied")
        else:
            self.message("Error: " + message_type)

    def message(self, message):
        for chat_id in self.chat_ids:
            self.bot.send_message(chat_id, message)

    # ---- All Bot Commands are here ---- #

    def initialize_bot(self, update, context):
        #Start Command: /start
       
        message = update.message
        username = message.from_user.first_name
        if self.correct_user(message):
            message.reply_text("Hello " + message.from_user.first_name)
            #bot.reply_to(message, "Hello " + message.from_user.first_name)

    def users(self, update, context):
        #Start Command: /users
        message = update.message
        if self.correct_user(message):
            message.reply_text(self.db.list_chat())
    
    def allow(self, update, context):
        #Start Command: /allow chat_id
        message = update.message

        strip_command = message.replace("/allow ", "").upper()
        order_params = strip_command.split()
        chat_id = int(order_params[0])
        if self.correct_user(message):
            allowusername = self.db.allow_chat(chat_id,True)
            self.message("from " + message.from_user.first_name+" \n "+ "allow "+ allowusername)
            #bot.reply_to(message, "Hello " + message.from_user.first_name)

    def deny(self, update, context):
        #Start Command: /deny chat_id
        message = update.message
        strip_command = message.replace("/allow ", "").upper()
        order_params = strip_command.split()
        chat_id = int(order_params[0])
        if self.correct_user(message):
            allowusername = self.db.allow_chat(chat_id,False)
            self.message("from " + message.from_user.first_name+" \n "+ "deny "+ allowusername)
            #bot.reply_to(message, "Hello " + message.from_user.first_name)



    def bot_info(self, update, context):
        #Help Command: /help
        message = update.message
        if self.correct_user(message):
            help = help_message()
            message.reply_text(help)
            #bot.reply_to(message, help)

    def make_market_order(self, update, context):
        #Market order: /market {side} {amount} {symbol}
        message = update.message
        if self.correct_user(message):
            try:
                order_confirmation = self.client.send_order("market", message)
                self.message("from " + message.from_user.first_name+" \n "+order_confirmation)
            except Exception as e:
                print(str(e))
                self.message("from " + message.from_user.first_name+" \n "+ self.general_error_message + "ex. /market buy 0.01 eth \n\n/market {side} {amount} {symbol}")
                #bot.reply_to(message, self.general_error_message + "ex. /market buy 0.01 eth \n\n/market {side} {amount} {symbol}")

    def make_limit_order(self, update, context):
        #Limit order: /limit {timeInForce} {side} {amount} {symbol} at {price}
        message = update.message
        if self.correct_user(message):
            try:
                order_confirmation = self.client.send_order("limit", message)
                self.message("from " + message.from_user.first_name+" \n "+ order_confirmation)
                #bot.reply_to(message, order_confirmation)
            except Exception as e:
                print(str(e))
                self.message("from " + message.from_user.first_name+" \n "+ self.general_error_message + "ex. /limit gtc sell 0.01 ethusdt at 1858 \n\n/limit {timeInForce} {side} {amount} {symbol} at {price}")
                #bot.reply_to(message, self.general_error_message + "ex. /limit gtc sell 0.01 ethusdt at 1858 \n\n/limit {timeInForce} {side} {amount} {symbol} at {price}")

    def make_stoploss_order(self, update, context):
        #'''Makes only one order: /stoploss {timeInForce} {side} {amount} {symbol} at {price} stop at {stopLoss}'''
        message = update.message
        if self.correct_user(message):
            try:
                order_confirmation = self.client.send_order("stoploss", message)
                self.message("from " + message.from_user.first_name+" \n "+ order_confirmation)
                #bot.reply_to(message, order_confirmation)
            except Exception as e:
                print(str(e))
                self.message("from " + message.from_user.first_name+" \n "+ self.general_error_message + "ex. /stoploss gtc sell 0.1 btc at 55000 stop at 56000\n\n /stoploss {timeInForce} {side} {amount} {symbol} at {price} stop at {stopLoss}")
                #bot.reply_to(message, self.general_error_message + "ex. /stoploss gtc sell 0.1 btc at 55000 stop at 56000\n\n /stoploss {timeInForce} {side} {amount} {symbol} at {price} stop at {stopLoss}")

    def current_price(self, update, context):
        #''' Checks current price of a token '''
        message = update.message
        if self.correct_user(message):
            try:
                quick_token_text = message.text.replace("/ticker", "").replace(" ", "").upper()
                if "USDT" in quick_token_text:
                    token = quick_token_text
                else:
                    token = quick_token_text + "USDT"
                link = self.ticker_link + token
                request = requests.get(link)
                data = request.json()
                message.reply_text(data['symbol'] + ": " + data['price'])
                #bot.reply_to(message, data['symbol'] + ": " + data['price'])
            except Exception as e:
                message.reply_text(self.general_error_message + "ex. /ticker btc or /ticker btcusdt")
                #bot.reply_to(message, self.general_error_message + "ex. /ticker btc or /ticker btcusdt")

    def show_order_history(self, update, context):
        #''' View order history: /orderhistory
        #Sends a csv of their past orders'''
        message = update.message
        if self.correct_user(message):
            try:
                if self.csv_file_name != None:
                    os.remove(self.csv_file_name) #Deletes file once sent
                    self.csv_file_name = None
                quick_token_text = message.text.replace("/orderhistory", "").replace(" ", "").upper()
                if "USDT" in quick_token_text:
                    token = quick_token_text
                else:
                    token = quick_token_text + "USDT"
                all_orders = self.client.see_all_orders(token)
                self.order_history_csv(token, all_orders)
                doc = open(self.csv_file_name, 'rb')
                self.bot.send_document(self.chat_id, doc)
            except Exception as e:
                print(str(e))
                message.reply_text(self.general_error_message + " AND make sure that you have made orders in the past using the token in question\n\nex. /orderhistory btc \n\n/orderhistory {symbol}")
                #bot.reply_to(message, self.general_error_message + "ex. /orderhistory btc \n\n/orderhistory {symbol}\n\nAlso make sure that you have made orders in the past using the token in question")

    def show_open_orders(self, update, context):
        #''' View open orders for a given token: /openorders {symbol}'''
        message = update.message
        if self.correct_user(message):
            try:
                quick_token_text = message.text.replace("/openorders", "").replace(" ", "").upper()
                if "USDT" in quick_token_text:
                    token = quick_token_text
                else:
                    token = quick_token_text + "USDT"
                open_orders = self.client.open_orders(token)
                self.open_orders_message_chain(open_orders, self.bot, token)
            except Exception as e:
                print(str(e))
                message.reply_text(self.general_error_message + "ex. /openorders eth\n\n/openorders {symbol}\n\nAlso make sure that you have made orders in the past using the token in question")
                #bot.reply_to(message, self.general_error_message + "ex. /openorders eth\n\n/openorders {symbol}\n\nAlso make sure that you have made orders in the past using the token in question")

    def cancel_order(self, update, context):
        #'''Cancels an order /cancel {symbol} {orderId}'''
        message = update.message
        if self.correct_user(message):
            try:
                cancelled_order = self.client.cancel_order(message)
                cancel_message = cancelled_message(cancelled_order)
                self.message("from " + message.from_user.first_name+" \n "+ cancel_message)
                #bot.reply_to(message, cancel_message)
            except Exception as e:
                print(str(e))
                self.message("from " + message.from_user.first_name+" \n "+ self.general_error_message + "ex. /cancel eth 6963\n\n/cancel {symbol} {order Id}\n\n")
                #bot.reply_to(message, self.general_error_message + "ex. /cancel eth 6963\n\n/cancel {symbol} {order Id}\n\n")

    def show_account(self, update, context):
        message = update.message
        if self.correct_user(message):
            info = self.client.get_account()
            message.reply_text(str(info))
            #bot.reply_to(message, str(info))

    def block_tradingview_orders(self, update, context):
        #''' Temporarily blocks tradingview orders '''
        message = update.message
        if self.correct_user(message):
            if self.block_tradingview:
                self.message("from " + message.from_user.first_name+" \n "+ "TradingView orders are already blocked. /unblock to continue TradingView orders")
                #bot.reply_to(message, "TradingView orders are already blocked. /unblock to continue TradingView orders")
            else:
                self.block_tradingview = True
                self.message("from " + message.from_user.first_name+" \n "+ "TradingView orders are now blocked. /unblock to continue TradingView orders")
                #bot.reply_to(message, "TradingView orders are now blocked. /unblock to continue TradingView orders")

    def unblock_tradingview_orders(self, update, context):
        #''' Unblocks tradingview orders '''
        message = update.message
        if self.correct_user(message):
            if self.block_tradingview:
                self.block_tradingview = False
                self.message("from " + message.from_user.first_name+" \n "+ "TradingView orders ready to continue. /block to block TradingView orders")
                #bot.reply_to(message, "TradingView orders ready to continue. /block to block TradingView orders")
            else:
                self.message("from " + message.from_user.first_name+" \n "+ "TradingView orders are currently active. /block to block TradingView orders")
                #bot.reply_to(message, "TradingView orders are currently active. /block to block TradingView orders")

    def kill_app(self, update, context):
        #''' Block TradingView orders and raises an Exception, killing the current Bot thread '''
        message = update.message
        self.message("from " + message.from_user.first_name+" \n "+ " block trading")  
        self.block_tradingview = True
        #self.bot_running = False
        #self.bot.stop_polling()
        pass
        #bot.send_message(0, message)

    def bot_commands(self):
        self.dp.add_handler(CommandHandler("start", self.initialize_bot))
        self.dp.add_handler(CommandHandler("help", self.bot_info))
        self.dp.add_handler(CommandHandler("market", self.make_market_order))
        self.dp.add_handler(CommandHandler("limit", self.make_limit_order))
        self.dp.add_handler(CommandHandler("stoploss", self.make_stoploss_order))
        self.dp.add_handler(CommandHandler("ticker", self.current_price))
        self.dp.add_handler(CommandHandler("orderhistory", self.show_order_history))
        self.dp.add_handler(CommandHandler("openorders", self.show_open_orders))
        self.dp.add_handler(CommandHandler("cancel", self.cancel_order))
        self.dp.add_handler(CommandHandler("account", self.show_account))
        self.dp.add_handler(CommandHandler("block", self.block_tradingview_orders))
        self.dp.add_handler(CommandHandler("unblock", self.unblock_tradingview_orders))
        self.dp.add_handler(CommandHandler("allow", self.allow))
        self.dp.add_handler(CommandHandler("deny", self.deny))
        self.dp.add_handler(CommandHandler("users", self.users))
        
        self.dp.add_handler(CommandHandler("kill", self.kill_app))

    # ----  ---- #

    # ---- Order History CSV ---- #
    def order_history_csv(self, token, order_history):
        filename = token + "_Order_History.csv"
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['Order ID',
                             'Client Order ID',
                             'Price',
                             'Original Quantity',
                             'Executed Quantity',
                             'Cummulative Quote Quantity',
                             'Status',
                             'Time In Force',
                             'Type',
                             'Side',
                             'Stop Price',
                             'Iceberg Quantity',
                             'Original Quote Order Quantity'])
        with open(filename, 'a') as f:
            writer = csv.writer(f)
            for order in order_history:
                writer.writerow([order['orderId'],
                                 order['clientOrderId'],
                                 order['price'],
                                 order['origQty'],
                                 order['executedQty'],
                                 order['cummulativeQuoteQty'],
                                 order['status'],
                                 order['timeInForce'],
                                 order['type'],
                                 order['side'],
                                 order['stopPrice'],
                                 order['icebergQty'],
                                 order['origQuoteOrderQty']])
        self.csv_file_name = filename
    # ---- ---- #

    # ---- Open Orders Message Chain ---- #
    def open_orders_message_chain(self, open_orders_list, bot, token):
        if len(open_orders_list) > 0:
            for order in open_orders_list:
                telegram_message = f"Order ID: {order['orderId']}\n" + f"Symbol: {order['symbol']}\n" + f"Price: {order['price']}\n" + f"Original Quantity: {order['origQty']}\n" + f"Executed Quantity: {order['executedQty']}\n" + f"Status: {order['status']}\n" + f"Type: {order['type']}\n" + f"Side: {order['side']}\n" + f"Time In Force: {order['timeInForce']}\n" + f"Stop Price: {order['stopPrice']}"
                self.message(telegram_message)
        else:
            self.message("You have no open orders for " + token)
    # ---- ---- #

    # ---- Async Polling Setup ---- #
    def polling(self):
        self.updater.start_polling()
        #self.updater.idle()

    def all_bot_actions(self):
        self.bot_commands()
        self.polling()

    def restart_async_polling(self):
        self.polling_thread = threading.Thread(target=self.all_bot_actions)
        self.polling_thread.start()

    def stop_async_polling(self):
        self.updater.stop_polling()
        self.polling_thread.join()

    # ---- ---- #
