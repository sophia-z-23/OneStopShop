## OneStopShop: accounts, postings, and customer profiles

Adds user accounts, business postings with image
uploads and time slots, and business-facing customer profiles to
OneStopShop

## Features

- **Join, log in, log out.** Users sign up as a business or a customer.
  Passwords are hashed with Passlib (argon2)
- **Business-only postings.** Logged-in businesses can post an *item*
  (title, price, optional image) or a *service* (title, optional price,
  optional image, and a time slot). Customers and logged-out users cannot access this feature.
- **My postings.** Each business can see a list of everything it has
  posted.
- **Customer profiles for businesses.** A business can see a customer's
  username, email, and contact info, along with that customer's bookings
  and inquiries with the business. Only businesses the customer has
  booked with or sent an inquiry to can see the profile.
- **Business profiles for customers.** A customer can see a businesses
  name, email, and contact info.
- **Search.** Customers can click on the search button on the main or  on their dashboard and search for businesses.

## Files

| `app.py` | Flask routes |
| `auth_db.py` | Password hashing and account queries (join, login) |
| `posting_db.py` | Posting, image, and time slot queries |
| `customer_db.py` | Customer profile, booking, and inquiry queries |
| `templates/join.html` | Sign-up form |
| `templates/login.html` | Login form |
| `templates/new_post.html` | Form for creating a posting |
| `templates/post.html` | One posting with its image, price, and time slots |
| `templates/my_postings.html` | A business's list of its postings |
| `templates/customer.html` | Customer profile as a business sees it |
| `templates/base.html` | Shared layout; the nav changes with login state |
| `uploads/` | Uploaded images, named by post id (files not committed to git) |
| `templates/business-profile.html` | A list of business information shown to the customer upon clicking on a search business |
| `templates/search.html` | Page where customers can search for businesses |
| `templates/customer-dash.html` | Customer dashboard |

## Routes

| Route | Who can use it | Purpose |
|---|---|---|
| `/join/` | anyone | Create a business or customer account |
| `/login/` | anyone | Log in |
| `/logout/` (POST) | logged in | Log out |
| `/post/new/` | businesses | Create a posting |
| `/my-postings/` | businesses | List your postings |
| `/post/<post_id>` | anyone | View a posting |
| `/post-image/<post_id>` | anyone | The image file for a posting |
| `/customer/<customer_id>` | businesses the customer has booked with or contacted | Customer profile |
| `/test-login/<account_id>` | anyone | **Testing only.** Logs in as any account without a password |
| `/search/` | customers | Search for businesses |
| `/getProfile/<business_name>` | customers | gets the profile of a business |

## Database changes

changes made to initial `szab304_db`:

```sql
alter table posting modify post_id int not null auto_increment;
alter table posting add column title varchar(100) after post_type;
alter table posting add column price decimal(8,2) after image_link;
alter table posting add column description varchar(500) after price;
alter table time_slot modify slot_id int not null auto_increment;

create table inquiry (
    inquiry_id int not null auto_increment primary key,
    customer_id int not null,
    post_id int not null,
    message varchar(1000),
    created_at timestamp default current_timestamp,
    foreign key (customer_id) references customers(account_id) on delete cascade,
    foreign key (post_id) references posting(post_id) on delete cascade
) engine = InnoDB;
```

How the tables are used:

- `posting.image_link` stores the uploaded file's name (for example
  `4.jpg`)
- A service's time slot is a row in `time_slot`. `customer_id` stays NULL
  until a customer books the slot.
- An inquiry links a customer to a posting. The business it went to is
  the posting's owner.


