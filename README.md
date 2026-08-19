# 🍔 FoodieHub – Online Food Ordering Website

FoodieHub is a responsive full-stack food ordering mini project built with **HTML, CSS, JavaScript, Python Flask and SQLite**. It includes customer authentication, menu search/filtering, a shopping cart, checkout, order history and an administrator dashboard.

## Features

### Customer
- Responsive landing page and menu
- Category filtering and food search
- Food cards with ratings and prices
- Add/update/remove cart items
- Checkout with delivery address and payment selection
- Order confirmation and order history
- Login and registration

### Admin
- Dashboard with customers, orders, revenue and menu statistics
- Add food items
- Delete food items
- View all orders
- Update order status

## Project Structure

```text
FoodieHub/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── menu.html
│   ├── _food_card.html
│   ├── cart.html
│   ├── checkout.html
│   ├── login.html
│   ├── register.html
│   ├── orders.html
│   ├── success.html
│   ├── admin.html
│   └── 404.html
└── static/
    ├── css/style.css
    ├── js/app.js
    └── images/
```

## Run Locally

1. Install Python 3.10+.
2. Open the project folder in VS Code.
3. Create and activate a virtual environment (optional but recommended):

```bash
python -m venv .venv
.venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Start the application:

```bash
python app.py
```

6. Open `http://127.0.0.1:5000` in your browser.

The SQLite database is created automatically on the first run.

## Demo Admin

- Email: `admin@foodiehub.com`
- Password: `admin123`

Change these credentials and the Flask secret key before using the project in production.

## GitHub Upload

```bash
git init
git add .
git commit -m "Initial FoodieHub project"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Notes

- Food images use external image URLs, so an internet connection is required for those images to display.
- This project is intended for academic/demo use. A production deployment should use environment variables for secrets, CSRF protection, a production database, secure session configuration and a real payment gateway.


## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

## Vercel Deployment

This project includes Vercel configuration for the Flask application.

1. Push the project files to GitHub.
2. Import the repository into Vercel.
3. Vercel will detect `vercel.json` and use `api/index.py`.
4. Deploy the project.

> Note: SQLite uses the deployment filesystem and is not suitable for persistent production data on Vercel. For persistent users, orders, and menu data, use an external database such as PostgreSQL or Supabase.
