from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
from datetime import datetime, timezone
from sqlalchemy import desc

app = Flask(__name__)
app.secret_key = 'secret_key_for_flashing'

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now())
    # Relationship with Comment
    comments = db.relationship('Comment', cascade="all, delete-orphan", backref='blog', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)  # Foreign Key
    name = db.Column(db.String(50), nullable=False)  # Name of the commenter
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now())  # Timestamp

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=True)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact_form.html')

@app.route('/resume')
def resume():
    return render_template('resume.html')

@app.route('/skills')
def skills():
    return render_template('skills.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

# Contacts
@app.route('/save_contact', methods=['POST'])
def save_contact():
    data = request.form  # Accept form data
    if not data or not all(key in data for key in ['name', 'email', 'phone', 'address']):
        flash("Invalid or incomplete data provided", 'error')
        return redirect(url_for('contact'))

    try:
        new_contact = Contact(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            address=data['address']
        )
        db.session.add(new_contact)
        db.session.commit()
        flash("Thank you for sharing. Your contact has been saved successfully!", 'success')
        return redirect(url_for('contact'))
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to save contact: {str(e)}", 'error')
        return redirect(url_for('contact'))

@app.route('/export_contacts', methods=['GET', 'POST'])
def export_contacts():
    #if request.method == 'POST':
    verification_key = request.form.get('verification_key')
    if verification_key != "myworld":
        flash(f"Wrong verification key. Please try again.:{verification_key}", 'error')
        return redirect(url_for('contact'))

    try:
        contacts = Contact.query.all()
        if not contacts:
            return jsonify({"error": "No contacts found to export"}), 404

        contacts_data = [{
            'ID': contact.id,
            'Name': contact.name,
            'Email': contact.email,
            'Phone': contact.phone,
            'Address': contact.address
        } for contact in contacts]

        file_path = 'contacts_export.xlsx'
        if os.path.exists(file_path):
            os.remove(file_path)  # Ensure previous file is deleted

        df = pd.DataFrame(contacts_data)
        df.to_excel(file_path, index=False, engine='openpyxl')

        response = send_file(file_path, as_attachment=True)
        return response
    except Exception as e:
        return jsonify({"error": "Failed to export contacts", "details": str(e)}), 500

# Blogs
@app.route('/blog_list')
def blog_list():
    blogs = Blog.query.order_by(desc(Blog.date_created)).all()  # Order by newest first
    return render_template('blog_list.html', blogs=blogs)

# Blog Details
@app.route('/blog_detail/<int:id>')
def blog_detail(id):
    blog = Blog.query.get_or_404(id)
    return render_template('blog_detail.html', blog=blog)

# Add Blog Post
@app.route('/add_blog', methods=['GET', 'POST'])
def add_blog():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        date_created = datetime.now()
        new_blog = Blog(title=title, content=content, date_created=date_created)
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('blog_list'))
    return render_template('add_blog.html')

# Delete Blog
@app.route('/delete_blog/<int:id>')
def delete_blog(id):
    blog = Blog.query.get_or_404(id)
    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for('blog_list'))

# Add comment
@app.route('/add_comment/<int:blog_id>', methods=['POST'])
def add_comment(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    name = request.form['name']
    content = request.form['content']
    new_comment = Comment(name=name, content=content, blog_id=blog.id)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('blog_detail', id=blog.id))


if __name__ == '__main__':
    app.run(debug=True)
