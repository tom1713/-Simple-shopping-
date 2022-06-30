# 初始化資料庫連線
from flask import *
from bson.objectid import ObjectId
import time
import pymongo
client = pymongo.MongoClient(
    "mongodb+srv://root:root123@cluster0.hpcbu.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.shop_system
print("資料庫連線建立成功")

# 初始化 flask 伺服器
app = Flask(
    __name__,
    static_folder="public",
    static_url_path="/"
)
app.secret_key = "123"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/adminsignup", methods=["GET", "POST"])
def adminsignup():
    if request.method == "POST":
        account = request.form["account"]
        password = request.form["password"]
        collection = db.admin_users
        collection.insert_one({
            "username": account,
            "password": password
        })
        flash("註冊成功")
    return render_template("adminsignup.html")

@app.route("/adminlogin", methods=["GET", "POST"])
def adminlogin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        collection = db.admin_users
        result = collection.find_one({
            "$and": [
                {"username": username},
                {"password": password}
            ]
        })
        if result == None:
            return "error"
        session["username"] = result["username"]
        return redirect("/admin")
    return render_template("adminlogin.html")

@app.route("/adminsignout")
def adminsignout():
    # 移除session中的會員資訊
    del session["username"]
    return redirect("/")

@app.route("/admin")
def admin():
    if "username" in session:
        collection = db.shopItem
        cur = collection.find()
        shopItem = cur
        return render_template("admin.html", shopItem=shopItem)
    return redirect("/")

@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        description = request.form["description"]
        stock = int(request.form["stock"])
        categoryId = int(request.form["categoryId"])
        date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        link = request.form["link"]
        collection = db.shopItem
        collection.insert_one({
            "name": name,
            "price": price,
            "description": description,
            "stock": stock,
            "categoryId": categoryId,
            "date": date,
            "link": link
        })
        return redirect("/admin")
    return render_template("add.html")

@app.route("/delete")
def delete():
    name = request.args.get("name")
    collection = db.shopItem
    result = collection.delete_one({
        "name": name
    })
    print("實際上刪除的資料有幾筆", result.deleted_count)
    return redirect("/admin")

@app.route("/update", methods=["GET", "POST"])
def update():
    name = request.args.get("name")
    if request.method == "POST":
        collection = db.shopItem
        name = request.form["name"]
        price = float(request.form["price"])
        description = request.form["description"]
        stock = int(request.form["stock"])
        categoryId = int(request.form["categoryId"])
        date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        link = request.form["link"]
        result = collection.update_one({
            "name": name
        }, {"$set": {
            "name": name,
            "price": price,
            "description": description,
            "stock": stock,
            "categoryId": categoryId,
            "date": date,
            "link": link
        }})
        print("符合條件的文件數量:", result.matched_count)
        return redirect("/admin")
    return render_template("update.html")

@app.route("/member")
def member():
    if "email" in session:
        collection = db.shopItem
        cur = collection.find()
        shopItem = cur
        return render_template("shop.html", shopItem=shopItem)
    else:
        return redirect("/")

# /error?msg=錯誤訊息
@app.route("/error")
def error():
    message = request.args.get("msg", "發生錯誤，請聯繫客服")
    return render_template("error.html", message=message)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    # 從前端接收資料
    if request.method == "POST":
        nickname = request.form["nickname"]
        email = request.form["email"]
        password = request.form["password"]
    # 根據收到的資料，跟資料庫互動
        collection = db.users
    # 檢查會員集合中是否有相同 email 的文件資料
        result = collection.find_one({
            "email": email
        })
        if result != None:
            return redirect("/error?msg=信箱已經被註冊")
    # 把資料放進資料庫，完成註冊
        collection.insert_one({
            "nickname": nickname,
            "email": email,
            "password": password
        })
        flash("註冊完成")
    return render_template("/signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # 從前端取得使用者的輸入
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
    # 和資料庫互動
        collection = db.users
    # 檢查信箱密碼是否正確
        result = collection.find_one({
            "$and": [
                {"email": email},
                {"password": password}
            ]
        })
    # 找不到對應的資料，登入失敗，導向到錯誤頁面
        if result == None:
            return redirect("/error?msg=帳號或密碼輸入錯誤")
    # 登入成功，導向到會員頁面
        session["email"] = result["email"]
        return redirect("/member")
    return render_template("login.html")


@app.route("/signout")
def signout():
    # 移除session中的會員資訊
    session.clear()
    return redirect("/")

cart_lists = []
products = []
price_list = []

@app.route("/addtocart", methods=["GET", "POST"])
def addtocart():
    if not "email" in session:
        return redirect("/")
    if request.method == "POST":
        quantity = int(request.form["quantity"])
        _id = request.form["_id"]
        collection = db.shopItem
        result = collection.find_one(ObjectId(_id))
        result["quantity"] = quantity
        if result == None:
            return redirect("/error?msg=無此產品")
        cart_lists.append({
            "_id": _id,
            "quantity": quantity
        })
        session["_id"] = []
        session["quantity"] = []
        session["price"] = []
        price = 0
        for cart_list in cart_lists:
            if session["_id"].count(_id) == 1:
                return redirect("/error?msg=已經加入購物車")
            else:
                session["_id"].append(format(cart_list["_id"]))
                session["quantity"].append(format(cart_list["quantity"]))
        if _id in session["_id"]:
            products.append(result)
        price = result["price"] * int(quantity)
        price_list.append(price)
        result["totalprice"] = price
    return redirect("/member")

@app.route("/mycart", methods=["GET", "POST"])
def mycart():
    if not "email" in session:
        return redirect("/")
    if not cart_lists:
        return redirect("/error?msg=購物車為空的")
    totalprice = 0
    for price in price_list:
        totalprice = totalprice + price
    return render_template("mycart.html", products=products, totalprice=totalprice)

@app.route("/delete_item")
def delete_item():
    totalprice = 0
    name = request.args.get("name")
    for x in products:
        for y in x.values():
            if name == y:
                price_list.remove(x["totalprice"])
                products.remove(x)
    for price in price_list:
        totalprice = totalprice + price
    return render_template("mycart.html", products=products, totalprice=totalprice)

@app.route("/to_pay", methods=["GET", "POST"])
def to_pay():
    totalprice = 0
    for price in price_list:
        totalprice = totalprice + price
    return render_template("to_pay.html", products=products, totalprice=totalprice)

# 載入 ECpay SDK
from werkzeug.security import generate_password_hash, check_password_hash
import collections
import hashlib
from urllib.parse import quote_plus
import os
import importlib.util
filename = os.path.dirname(os.path.realpath(__file__))
spec = importlib.util.spec_from_file_location(
    "ecpay_payment_sdk", filename + "/sdk/ecpay_payment_sdk.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from datetime import datetime

# payment = Blueprint('payment', __name__)

class Params:
    def __init__(self):
        web_type = 'test'
        if web_type == 'offical':
            # 正式環境
            self.params = {
                'MerchantID': '隱藏',
                'HashKey': '隱藏',
                'HashIV': '隱藏',
                'action_url':
                'https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5'
            }
        else:
            # 測試環境
            self.params = {
                'MerchantID':
                '2000132',
                'HashKey':
                '5294y06JbISpM5x9',
                'HashIV':
                'v77hoKGq4kWxNNIS',
                'action_url':
                'https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5'
            }
    @classmethod
    def get_params(cls):
        return cls().params

    # 驗證綠界傳送的 check_mac_value 值是否正確
    @classmethod
    def get_mac_value(cls, get_request_form):
        params = dict(get_request_form)
        if params.get('CheckMacValue'):
            params.pop('CheckMacValue')
        ordered_params = collections.OrderedDict(
            sorted(params.items(), key=lambda k: k[0].lower()))
        HahKy = cls().params['HashKey']
        HashIV = cls().params['HashIV']
        encoding_lst = []
        encoding_lst.append('HashKey=%s&' % HahKy)
        encoding_lst.append(''.join([
            '{}={}&'.format(key, value)
            for key, value in ordered_params.items()
        ]))
        encoding_lst.append('HashIV=%s' % HashIV)
        safe_characters = '-_.!*()'
        encoding_str = ''.join(encoding_lst)
        encoding_str = quote_plus(str(encoding_str),
                                  safe=safe_characters).lower()
        check_mac_value = ''
        check_mac_value = hashlib.sha256(
            encoding_str.encode('utf-8')).hexdigest().upper()
        return check_mac_value

# 建立訂單後跳轉至 ECpay 頁面
@app.route("/to_ecpay", methods=["POST"])
def to_ecpay():
    # 從 session 中取得 uid
    uid = session["email"]
    host_name = request.host_url
    print (host_name)
    # 取得 POST 的收件人資訊
    # trade_name = request.values.get("name")
    # trade_phone = request.values.get("phone")
    # 利用 uid 查詢資料庫，購物車商品 & 價錢
    totalprice = 0
    total_product_name = ''
    for price in price_list:
        totalprice = totalprice + price
    for product in products:
        price = product["price"]
        product_name = product["name"]
        quan = product["quantity"]
        total_product_name += product_name + '#'
    # 建立交易編號 tid
    date = time.time()
    tid = str(date) + 'Uid' + str(uid)
    status = '未刷卡'
    # 新增 Transaction 訂單資料
    # T = sql.Transaction(uid, tid, trade_name, trade_phone, address,
    #                     total_product_price, status, county, district, zipcode)
    # db.session.add(T)
    # db.session.commit()
    params = Params.get_params()
    # 設定傳送給綠界參數
    order_params = {
        'MerchantTradeNo': datetime.now().strftime("NO%Y%m%d%H%M%S"),
        'StoreID': '',
        'MerchantTradeDate': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        'PaymentType': 'aio',
        'TotalAmount': int(totalprice),
        "TradeDesc": "ToolsFactory",
        "ItemName": total_product_name,
        "ReturnURL": host_name + "receive_result",
        "ChoosePayment": "Credit",
        "ClientBackURL": host_name + "trad_result",
        "Remark": "交易備註",
        "ChooseSubPayment": "",
        "OrderResultURL": host_name + "trad_result",
        "NeedExtraPaidInfo": "Y",
        "DeviceSource": "",
        "IgnorePayment": "",
        "PlatformID": "",
        "InvoiceMark": "N",
        'CustomField1': str(tid),
        'CustomField2': '',
        'CustomField3': '',
        'CustomField4': '',
        'EncryptType': 1,
    }
    extend_params_1 = {
        'BindingCard': 0,
        'MerchantMemberID': '',
    }
    extend_params_2 = {
        'Redeem': 'N',
        'UnionPay': 0,
    }
    inv_params = {
        # 'RelateNumber': 'Tea0001', # 特店自訂編號
        # 'CustomerID': 'TEA_0000001', # 客戶編號
        # 'CustomerIdentifier': '53348111', # 統一編號
        # 'CustomerName': '客戶名稱',
        # 'CustomerAddr': '客戶地址',
        # 'CustomerPhone': '0912345678', # 客戶手機號碼
        # 'CustomerEmail': 'abc@ecpay.com.tw',
        # 'ClearanceMark': '2', # 通關方式
        # 'TaxType': '1', # 課稅類別
        # 'CarruerType': '', # 載具類別
        # 'CarruerNum': '', # 載具編號
        # 'Donation': '1', # 捐贈註記
        # 'LoveCode': '168001', # 捐贈碼
        # 'Print': '1',
        # 'InvoiceItemName': '測試商品1|測試商品2',
        # 'InvoiceItemCount': '2|3',
        # 'InvoiceItemWord': '個|包',
        # 'InvoiceItemPrice': '35|10',
        # 'InvoiceItemTaxType': '1|1',
        # 'InvoiceRemark': '測試商品1的說明|測試商品2的說明',
        # 'DelayDay': '0', # 延遲天數
        # 'InvType': '07', # 字軌類別
    }
    ecpay_payment_sdk = module.ECPayPaymentSdk(MerchantID=params['MerchantID'],
                                               HashKey=params['HashKey'],
                                               HashIV=params['HashIV'])
    # 合併延伸參數
    order_params.update(extend_params_1)
    order_params.update(extend_params_2)
    # 合併發票參數
    order_params.update(inv_params)
    try:
        # 產生綠界訂單所需參數
        final_order_params = ecpay_payment_sdk.create_order(order_params)
        # 產生 html 的 form 格式
        action_url = params['action_url']
        html = ecpay_payment_sdk.gen_html_post_form(
            action_url, final_order_params)
        return html
    except Exception as error:
        print("An exception happened: " + str(error))

# ReturnURL: 綠界 Server 端回傳 (POST)
@app.route("/receive_result", methods=["POST"])
def end_return():
    result = request.form["RtnMsg"]
    tid = request.form["CustomField1"]
    return "1|OK"

# OrderResultURL: 綠界 Client 端 (POST)
@app.route("/trad_result", methods=["GET", "POST"])
def end_page():
    if request.method == "GET":
        return redirect(url_for("index"))
    if request.method == "POST":
        check_mac_value = Params.get_mac_value(request.form)
        if request.form["CheckMacValue"] != check_mac_value:
            return "請聯繫管理員"
        # 接收 ECpay 刷卡回傳資訊
        result = request.form["RtnMsg"]
        tid = request.form['CustomField1']
        # 判斷成功
        if result == "Succeeded":
            commit_list = []
            # 讀取訂單細項資料
            return render_template("/successful.html")
        # 判斷失敗
        else:
            return render_template("/error?msg=付款失敗")
app.run()
#debug=True