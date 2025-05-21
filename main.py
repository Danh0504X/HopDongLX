
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Contract, Customer, Money
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your-secret-key'
db.init_app(app)

def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

init_db()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    identifier = request.form.get('identifier')  # username or email
    password = request.form.get('password')
    
    user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
    
    if user and user.password == password:
        session['username'] = user.username
        return redirect(url_for('welcome'))
    
    flash('Tài khoản hoặc mật khẩu không đúng hoặc tài khoản không tồn tại')
    return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return redirect(url_for('signup'))
        
    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    
    flash('Tạo tài khoản thành công')
    return redirect(url_for('login'))

@app.route('/welcome')
def welcome():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    contracts_count = Contract.query.filter_by(driver_username=user.username).count()
    customers_count = Customer.query.join(Contract).filter(Contract.driver_username == user.username).distinct().count()
    return render_template('welcome.html', user=user, contracts_count=contracts_count, customers_count=customers_count)

@app.route('/add_contract', methods=['GET', 'POST'])
def add_contract():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        # Kiểm tra khách hàng đã tồn tại
        existing_customer = Customer.query.filter_by(id_number=request.form['id_number']).first()
        
        if existing_customer:
            customer = existing_customer
        else:
            # Tạo customer mới nếu chưa tồn tại
            customer = Customer(
                name=request.form['customer_name'],
                id_number=request.form['id_number'],
                phone=request.form['phone']
            )
            db.session.add(customer)
            db.session.commit()
        
        # Tạo contract mới
        contract = Contract(
            contract_number=request.form['contract_number'],
            customer_id=customer.id,
            driver_username=session['username'],
            pickup_location=request.form['pickup_location'],
            dropoff_location=request.form['dropoff_location'],
            contract_date=datetime.strptime(request.form['contract_date'], '%Y-%m-%d').date()
        )
        db.session.add(contract)
        db.session.commit()
        
        def convert_money_string(money_str):
            money_str = money_str.lower().strip()
            # Remove common currency symbols and separators
            money_str = money_str.replace('đồng', '').replace('vnđ', '').replace(',', '').strip()
            
            multiplier = 1
            if 'triệu' in money_str or 'tr' in money_str:
                multiplier = 1000000
                money_str = money_str.replace('triệu', '').replace('tr', '')
            elif 'k' in money_str or 'ngàn' in money_str:
                multiplier = 1000
                money_str = money_str.replace('k', '').replace('ngàn', '')
                
            try:
                number = float(money_str.strip())
                return number * multiplier
            except:
                flash('Số tiền không hợp lệ')
                return None

        total_amount = convert_money_string(request.form['total_amount'])
        deposit = convert_money_string(request.form['deposit'] or '0')

        if not total_amount:
            return redirect(url_for('add_contract'))

        if deposit and deposit >= total_amount:
            flash('Tiền cọc phải nhỏ hơn tổng tiền')
            return redirect(url_for('add_contract'))

        # Tạo money record
        money = Money(
            contract_id=contract.id,
            total_amount=total_amount,
            deposit=deposit or 0
        )
        db.session.add(money)
        db.session.commit()
        
        return redirect(url_for('welcome'))
        
    return render_template('add_contract.html')

@app.route('/search_contracts')
def search_contracts():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    customer_name = request.args.get('customer_name')
    phone = request.args.get('phone')
    contract_number = request.args.get('contract_number')
    created_date = request.args.get('created_date')
    
    query = Contract.query.join(Customer)
    
    if customer_name:
        query = query.filter(Customer.name.ilike(f'%{customer_name}%'))
    if phone:
        query = query.filter(Customer.phone.ilike(f'%{phone}%'))
    if contract_number:
        query = query.filter(Contract.contract_number.ilike(f'%{contract_number}%'))
    if created_date:
        date_obj = datetime.strptime(created_date, '%Y-%m-%d')
        query = query.filter(db.func.date(Contract.created_at) == date_obj.date())
    
    contracts = query.all() if any([customer_name, phone, contract_number, created_date]) else Contract.query.all()
    return render_template('search_contracts.html', contracts=contracts)

@app.route('/contract_detail/<int:contract_id>')
def contract_detail(contract_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    contract = Contract.query.get_or_404(contract_id)
    return render_template('contract_detail.html', contract=contract)

@app.route('/update_contract/<int:contract_id>', methods=['POST'])
def update_contract(contract_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    contract = Contract.query.get_or_404(contract_id)
    contract.contract_number = request.form['contract_number'] or None
    contract.pickup_location = request.form['pickup_location']
    contract.dropoff_location = request.form['dropoff_location']
    
    contract.customer.name = request.form['customer_name']
    contract.customer.id_number = request.form['id_number']
    contract.customer.phone = request.form['phone']
    
    total_amount = convert_money_string(request.form['total_amount'])
    deposit = convert_money_string(request.form['deposit'] or '0')
    
    if not total_amount:
        return redirect(url_for('contract_detail', contract_id=contract_id))
        
    if deposit and deposit >= total_amount:
        flash('Tiền cọc phải nhỏ hơn tổng tiền')
        return redirect(url_for('contract_detail', contract_id=contract_id))
        
    contract.money.total_amount = total_amount
    contract.money.deposit = deposit
    
    db.session.commit()
    flash('Cập nhật hợp đồng thành công')
    return redirect(url_for('contract_detail', contract_id=contract_id))

@app.route('/delete_contract/<int:contract_id>')
def delete_contract(contract_id):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    contract = Contract.query.get_or_404(contract_id)
    db.session.delete(contract)
    db.session.commit()
    flash('Đã xóa hợp đồng')
    return redirect(url_for('search_contracts'))

@app.route('/contract_list')
def contract_list():
    return "Coming soon"

@app.route('/customer_list')
def customer_list():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    customers = db.session.query(
        Customer,
        db.func.count(Contract.id).label('contract_count'),
        db.func.sum(Money.total_amount).label('total_spending')
    ).join(Contract, Customer.id == Contract.customer_id)\
     .join(Money, Contract.id == Money.contract_id)\
     .group_by(Customer.id).all()
    
    customer_data = []
    for customer, contract_count, total_spending in customers:
        customer_data.append({
            'name': customer.name,
            'phone': customer.phone,
            'contract_count': contract_count,
            'total_spending': total_spending or 0
        })
    
    return render_template('customer_list.html', customers=customer_data)

@app.route('/income')
def income():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Tính thu nhập tháng này
    monthly_income = db.session.query(db.func.sum(Money.total_amount))\
        .join(Contract)\
        .filter(Contract.driver_username == session['username'])\
        .filter(db.extract('month', Contract.contract_date) == current_month)\
        .filter(db.extract('year', Contract.contract_date) == current_year)\
        .scalar() or 0
    
    # Tính thu nhập năm nay
    yearly_income = db.session.query(db.func.sum(Money.total_amount))\
        .join(Contract)\
        .filter(Contract.driver_username == session['username'])\
        .filter(db.extract('year', Contract.contract_date) == current_year)\
        .scalar() or 0
    
    return render_template('income.html',
                         monthly_income=monthly_income,
                         yearly_income=yearly_income,
                         current_month=current_month,
                         current_year=current_year)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
