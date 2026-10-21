import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'kicksstore_secret_key_ets'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

data_sepatu = [
    {"id": 1, "nama": "Nike Air Force 1 '07", "kategori": "Lifestyle", "harga": 1549000, "harga_fmt": "1.549.000", "stok": 12, "gambar": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=500"},
    {"id": 2, "nama": "Adidas Ultraboost Light", "kategori": "Running", "harga": 2800000, "harga_fmt": "2.800.000", "stok": 8, "gambar": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=500"},
    {"id": 3, "nama": "Puma Suede Classic", "kategori": "Casual", "harga": 1099000, "harga_fmt": "1.099.000", "stok": 0, "gambar": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=500"},
    {"id": 4, "nama": "New Balance 550", "kategori": "Retro", "harga": 1999000, "harga_fmt": "1.999.000", "stok": 5, "gambar": "https://images.unsplash.com/photo-1539185441755-769473a23570?w=500"}
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/produk')
def produk():
    return render_template('produk.html', sepatu_list=data_sepatu)

@app.route('/tambah-produk', methods=['GET', 'POST'])
def tambah_produk():
    if request.method == 'POST':
        nama = request.form.get('nama')
        kategori = request.form.get('kategori')
        harga_raw = request.form.get('harga', '0').replace('.', '').replace(',', '')
        try:
            harga_num = int(harga_raw)
        except ValueError:
            harga_num = 0
        harga_fmt = f"{harga_num:,}".replace(',', '.')
        stok = request.form.get('stok')
        
        file = request.files.get('gambar')
        gambar_path = "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500"
        
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            gambar_path = url_for('static', filename=f'uploads/{filename}')

        new_id = max([item['id'] for item in data_sepatu], default=0) + 1
        data_sepatu.append({
            "id": new_id,
            "nama": nama,
            "kategori": kategori,
            "harga": harga_num,
            "harga_fmt": harga_fmt,
            "stok": int(stok) if stok else 0,
            "gambar": gambar_path
        })
        flash('Produk sepatu berhasil ditambahkan!', 'success')
        return redirect(url_for('produk'))
        
    return render_template('tambah_produk.html')

# Fitur Hapus Produk Per Satuan
@app.route('/hapus-produk/<int:sepatu_id>')
def hapus_produk(sepatu_id):
    global data_sepatu
    data_sepatu = [item for item in data_sepatu if item['id'] != sepatu_id]
    flash('Produk sepatu berhasil dihapus dari katalog!', 'warning')
    return redirect(url_for('produk'))

# Fitur Bersihkan Semua Sepatu dengan Stok Habis (stok == 0)
@app.route('/hapus-stok-habis')
def hapus_stok_habis():
    global data_sepatu
    data_sepatu = [item for item in data_sepatu if item.get('stok', 0) > 0]
    flash('Semua sepatu dengan stok habis telah berhasil dibersihkan!', 'warning')
    return redirect(url_for('produk'))

# Fitur Keranjang Belanja (Add to Cart)
@app.route('/tambah-keranjang/<int:sepatu_id>')
def tambah_keranjang(sepatu_id):
    sepatu = next((item for item in data_sepatu if item['id'] == sepatu_id), None)
    if not sepatu or sepatu.get('stok', 0) <= 0:
        flash('Maaf, stok sepatu ini telah habis!', 'danger')
        return redirect(url_for('produk'))

    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    str_id = str(sepatu_id)
    cart[str_id] = cart.get(str_id, 0) + 1
    session['cart'] = cart
    session.modified = True
    flash('Sepatu berhasil dimasukkan ke keranjang belanja!', 'info')
    return redirect(url_for('keranjang'))

# Halaman Lihat Keranjang Belanja
@app.route('/keranjang')
def keranjang():
    cart = session.get('cart', {})
    items = []
    total_harga = 0
    total_items = 0
    
    for str_id, qty in cart.items():
        s_id = int(str_id)
        sepatu = next((item for item in data_sepatu if item['id'] == s_id), None)
        if sepatu:
            subtotal = sepatu['harga'] * qty
            total_harga += subtotal
            total_items += qty
            items.append({
                'sepatu': sepatu,
                'qty': qty,
                'subtotal': subtotal,
                'subtotal_fmt': f"{subtotal:,}".replace(',', '.')
            })
            
    total_harga_fmt = f"{total_harga:,}".replace(',', '.')
    return render_template('keranjang.html', items=items, total_harga=total_harga_fmt, total_items=total_items)

# Hapus item dari keranjang
@app.route('/hapus-keranjang/<int:sepatu_id>')
def hapus_keranjang(sepatu_id):
    cart = session.get('cart', {})
    str_id = str(sepatu_id)
    if str_id in cart:
        del cart[str_id]
        session['cart'] = cart
        session.modified = True
        flash('Item berhasil dihapus dari keranjang.', 'warning')
    return redirect(url_for('keranjang'))

# Halaman Checkout
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Keranjang Anda masih kosong!', 'warning')
        return redirect(url_for('produk'))
        
    items = []
    total_harga = 0
    for str_id, qty in cart.items():
        s_id = int(str_id)
        sepatu = next((item for item in data_sepatu if item['id'] == s_id), None)
        if sepatu:
            subtotal = sepatu['harga'] * qty
            total_harga += subtotal
            items.append({
                'sepatu': sepatu,
                'qty': qty,
                'subtotal': subtotal,
                'subtotal_fmt': f"{subtotal:,}".replace(',', '.')
            })
            
    total_harga_fmt = f"{total_harga:,}".replace(',', '.')

    if request.method == 'POST':
        session.pop('cart', None) # Kosongkan keranjang setelah checkout
        nama_pemesan = request.form.get('nama_pembeli')
        return render_template('sukses_checkout.html', nama=nama_pemesan, total=total_harga_fmt)

    return render_template('checkout.html', items=items, total_harga=total_harga_fmt)

@app.route('/profil')
def profil():
    return render_template('profil.html')

if __name__ == '__main__':
    app.run(debug=True)
