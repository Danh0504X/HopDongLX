from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Contract, Customer, Money
from datetime import datetime
import sqlalchemy
import traceback

app = Flask(__name__)
# Kết nối SQL Server với ODBC Driver 17
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17 for SQL Server};SERVER=LEGION5-9FN5TV5\\SQLEXPRESS;DATABASE=DriveContract;Trusted_Connection=yes'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
db.init_app(app)

def init_db():
    with app.app_context():
        try:
            # Kiểm tra kết nối database
            result = db.session.execute(sqlalchemy.text('SELECT @@VERSION')).scalar()
            print("Database connection successful!")
            print(f"SQL Server version: {result}")
            
            # Drop các bảng theo thứ tự đúng
            print("Dropping existing tables...")
            db.session.execute(sqlalchemy.text('DROP TABLE IF EXISTS money'))
            db.session.execute(sqlalchemy.text('DROP TABLE IF EXISTS contracts'))
            db.session.execute(sqlalchemy.text('DROP TABLE IF EXISTS customers'))
            db.session.execute(sqlalchemy.text('DROP TABLE IF EXISTS users'))
            db.session.commit()
            print("Dropped all existing tables")
            
            # Tạo bảng users bằng SQL trực tiếp
            print("Creating users table...")
            db.session.execute(sqlalchemy.text("""
                CREATE TABLE users (
                    username VARCHAR(80) PRIMARY KEY,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password VARCHAR(120) NOT NULL,
                    full_name VARCHAR(120),
                    birth_date DATE,
                    id_number VARCHAR(20),
                    phone VARCHAR(15),
                    created_at DATETIME DEFAULT GETDATE(),
                    is_driver BIT DEFAULT 0
                )
            """))
            db.session.commit()
            print("Created users table")
            
            # Tạo các bảng còn lại bằng SQLAlchemy
            db.create_all()
            print("All tables created successfully!")
            
        except Exception as e:
            print(f"Database error: {str(e)}")
            print("Full error traceback:")
            print(traceback.format_exc())
            raise e

# Thêm hàm để kiểm tra và tạo bảng nếu chưa tồn tại
def check_and_create_tables():
    with app.app_context():
        try:
            # Kiểm tra kết nối database
            result = db.session.execute(sqlalchemy.text('SELECT @@VERSION')).scalar()
            print("✅ Kết nối database thành công!")
            print(f"SQL Server version: {result}")
            
            # Kiểm tra xem bảng users đã tồn tại chưa
            result = db.session.execute(sqlalchemy.text("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'users'
            """)).scalar()
            
            if result == 0:
                print("🔄 Tạo bảng users...")
                db.session.execute(sqlalchemy.text("""
                    CREATE TABLE users (
                        username VARCHAR(80) PRIMARY KEY,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        password VARCHAR(120) NOT NULL,
                        full_name VARCHAR(120),
                        birth_date DATE,
                        id_number VARCHAR(20),
                        phone VARCHAR(15),
                        created_at DATETIME DEFAULT GETDATE(),
                        is_driver BIT DEFAULT 0
                    )
                """))
                db.session.commit()
                print("✅ Đã tạo bảng users")
            else:
                print("✅ Bảng users đã tồn tại")
            
            # Tạo các bảng khác nếu chưa có
            db.create_all()
            print("✅ Kiểm tra và tạo bảng hoàn tất!")
            
        except Exception as e:
            print(f"❌ Lỗi database: {str(e)}")
            print("Chi tiết lỗi:")
            print(traceback.format_exc())
            raise e

# Thêm hàm để reset database
def reset_database():
    with app.app_context():
        try:
            print("🔄 Đang xóa tất cả bảng...")
            db.session.execute(sqlalchemy.text('DROP TABLE IF EXISTS money'))
            db.session.execute(sqlalchemy.text('DROP TABLE IF EXISTS contracts'))
            db.session.execute(sqlalchemy.text('DROP TABLE IF EXISTS customers'))
            db.session.execute(sqlalchemy.text('DROP TABLE IF EXISTS users'))
            db.session.commit()
            print("✅ Đã xóa tất cả bảng")
            
            # Tạo lại các bảng
            check_and_create_tables()
            print("✅ Reset database thành công!")
            
        except Exception as e:
            print(f"❌ Lỗi khi reset database: {str(e)}")
            print("Chi tiết lỗi:")
            print(traceback.format_exc())
            raise e

# Khởi tạo database khi chạy app
if __name__ == '__main__':
    # Uncomment dòng dưới nếu muốn reset database mỗi khi chạy app
    # reset_database()
    
    # Hoặc chỉ kiểm tra và tạo bảng nếu chưa có
    check_and_create_tables()
    app.run(host='0.0.0.0', port=5000)

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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
        
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Validate required fields
            if not all([username, email, password, confirm_password]):
                flash("Vui lòng điền đầy đủ thông tin", "danger")
                return render_template('signup.html')

            # Kiểm tra mật khẩu xác nhận
            if password != confirm_password:
                flash("Mật khẩu xác nhận không khớp", "danger")
                return render_template('signup.html')

            # Kiểm tra username hoặc email đã tồn tại
            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                if existing_user.username == username:
                    flash(f"Tên đăng nhập '{username}' đã được sử dụng. Vui lòng chọn tên đăng nhập khác.", "danger")
                else:
                    flash(f"Email '{email}' đã được đăng ký. Vui lòng sử dụng email khác.", "danger")
                return render_template('signup.html')

            # Tạo user mới
            new_user = User(username=username, email=email, password=password, is_driver=True)
            db.session.add(new_user)
            db.session.commit()

            flash("✅ Tạo tài khoản thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            error_message = str(e)
            print(f"❌ Lỗi database: {error_message}")
            print("Chi tiết lỗi:")
            print(traceback.format_exc())
            
            flash(f"❌ Lỗi khi tạo tài khoản: {error_message}", "danger")
            return render_template('signup.html')

    return render_template('signup.html')

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
            contract_date=datetime.strptime(request.form['contract_date'], '%Y-%m-%d').date(),
            pickup_time=datetime.strptime(request.form['pickup_time'], '%H:%M').time()
        )
        db.session.add(contract)
        db.session.commit()
        
        def convert_money_string(money_str):
            if not money_str:
                return 0
            
            try:
                # Chuyển tất cả về string và loại bỏ khoảng trắng
                money_str = str(money_str).strip().lower()
                
                # Loại bỏ các ký tự tiền tệ và phân cách
                money_str = money_str.replace('đồng', '')\
                                   .replace('vnđ', '')\
                                   .replace('vnd', '')\
                                   .replace(',', '')\
                                   .replace('.', '')\
                                   .strip()
                
                # Xử lý các đơn vị
                multiplier = 1
                if any(unit in money_str for unit in ['triệu', 'tr']):
                    multiplier = 1000000
                    money_str = money_str.replace('triệu', '').replace('tr', '')
                elif any(unit in money_str for unit in ['k', 'nghìn', 'ngàn']):
                    multiplier = 1000
                    money_str = money_str.replace('k', '')\
                                       .replace('nghìn', '')\
                                       .replace('ngàn', '')
                    
                # Chuyển về số và nhân với hệ số
                number = float(money_str.strip())
                result = number * multiplier
                
                # Kiểm tra kết quả hợp lệ
                if result <= 0:
                    flash('Số tiền phải lớn hơn 0')
                    return None
                    
                return result
                
            except (ValueError, TypeError):
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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        user.full_name = request.form['full_name']
        user.birth_date = datetime.strptime(request.form['birth_date'], '%Y-%m-%d') if request.form['birth_date'] else None
        user.id_number = request.form['id_number']
        user.phone = request.form['phone']
        db.session.commit()
        flash('Cập nhật thông tin thành công')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user)

@app.route('/customer_list')
def customer_list():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Truy vấn danh sách khách đã có hợp đồng
    customers = db.session.query(
        Customer.id,
        Customer.name,
        Customer.id_number,
        Customer.phone,
        db.func.count(Contract.id).label('contract_count'),
        db.func.sum(Money.total_amount).label('total_spending')
    ).join(Contract, Customer.id == Contract.customer_id)\
     .join(Money, Contract.id == Money.contract_id)\
     .filter(Contract.driver_username == session['username'])\
     .group_by(Customer.id, Customer.name, Customer.id_number, Customer.phone)\
     .having(db.func.count(Contract.id) > 0)\
     .all()
    
    # Đưa dữ liệu ra dạng dict dễ dùng trong HTML
    customer_data = []
    for id, name, id_number, phone, contract_count, total_spending in customers:
        customer_data.append({
            'id': id,
            'name': name,
            'id_number': id_number,
            'phone': phone,
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
    
    # Khởi tạo mảng monthly_data với 12 phần tử bằng 0
    monthly_data = [0] * 12
    
    # Lấy dữ liệu thu nhập theo từng tháng
    monthly_incomes = db.session.query(
        db.func.extract('month', Contract.contract_date).label('month'),
        db.func.sum(Money.total_amount).label('total')
    ).join(Contract)\
    .filter(Contract.driver_username == session['username'])\
    .filter(db.extract('year', Contract.contract_date) == current_year)\
    .group_by(db.func.extract('month', Contract.contract_date))\
    .all()
    
    # Cập nhật dữ liệu vào mảng monthly_data
    for month, total in monthly_incomes:
        if month and total:  # Kiểm tra dữ liệu hợp lệ
            monthly_data[int(month) - 1] = float(total)
    
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
    
    # Số hợp đồng tháng này
    monthly_contracts = db.session.query(db.func.count(Contract.id))\
        .filter(Contract.driver_username == session['username'])\
        .filter(db.extract('month', Contract.contract_date) == current_month)\
        .filter(db.extract('year', Contract.contract_date) == current_year)\
        .scalar() or 0
    
    # Số hợp đồng năm nay
    yearly_contracts = db.session.query(db.func.count(Contract.id))\
        .filter(Contract.driver_username == session['username'])\
        .filter(db.extract('year', Contract.contract_date) == current_year)\
        .scalar() or 0
    
    # Thu nhập trung bình mỗi hợp đồng
    average_income = yearly_income / yearly_contracts if yearly_contracts > 0 else 0
    
    # Tổng tiền cọc
    total_deposit = db.session.query(db.func.sum(Money.deposit))\
        .join(Contract)\
        .filter(Contract.driver_username == session['username'])\
        .filter(db.extract('year', Contract.contract_date) == current_year)\
        .scalar() or 0
    
    return render_template('income.html',
                         monthly_income=monthly_income,
                         yearly_income=yearly_income,
                         monthly_contracts=monthly_contracts,
                         yearly_contracts=yearly_contracts,
                         average_income=average_income,
                         total_deposit=total_deposit,
                         monthly_data=monthly_data,
                         current_month=current_month,
                         current_year=current_year)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))
