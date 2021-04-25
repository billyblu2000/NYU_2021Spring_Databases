# Databases Final Project Manual

Authored by Billy Yi[^1] and Ziyang Liao[^2]



## Catalogue

[TOC]

## Project Structure

```python
.
├── README.md                      # A project discreption
├── app.py                         # A project discreption
├── config.py                      # A project discreption
├── make_data.py                   # A project discreption
├── mysql_tool.py                  # A project discreption
├── static
│   ├── css
│   │   └── bootstrap.css          # A project discreption
│   ├── favicon.ico                # A project discreption
│   ├── img
│   │   └── banner-bg.jpg          # A project discreption
│   └── js
│       └── bootstrap.min.js       # A project discreption
├── templates
│   ├── admin.html                 # A project discreption
│   ├── admin_s.html
│   ├── home.html
│   ├── index_old.html
│   ├── login.html
│   ├── register-agent.html
│   ├── register-customer.html
│   └── register-staff.html
└── utils.py
```





## Function Introduction and Usage



### General Discreption

This web application is a demo of a flight ticket reservation system, implemented by Python/Flask and  MySQL at the back-end, and Bootstrap CSS framework at the front-end. The application provides different functions for three kinds of users: customer, booking agent and airline staff. Generally, customers and booking agents can reserve or book flight tickets via the system, and airline staff can insert and update informations of flights and airplanes. Detailed functions will be provided in the later paragraphs. 

You can start the application by running `app.py`  using a Python interpreter. By default, the application will be running on localhost, port 80. After the app starts, hosts that are in the same LAN should be able to access the application by entering your local IP (LAN IP) in their browser. If you want to access only from localhost, you can change `DEBUG = False` to `DEBUG = True` in the file `config.py`.

After the application starts, you can type [localhost/](localhost/) or LAN IP in the address, the application will automatically redirect to [localhost/home/](localhost/home/) to view the home page. (Please notice that if you switch to `DEBUG = True`, you should type [localhost:5000/](localhost:5000/) in your address because the application is now running on port 5000). In our project, MySQL server is running on an Internet remote server (Tencent Cloud), so in order to better manage the database, we have also provided a webpage ([localhost/admin/](localhost/admin/)) for developers to run SQL and fetch results if any.



### Functions for Different Roles

##### Public (Guest)

`SELECT * FROM airline`

`SELECT * FROM flight WHERE customer_name = 'ly1387@nyu.edu'`



##### Login and Register



##### Users

###### Customer



###### Booking Agent



###### Airline Staff



## Acknowledge

Special thanks to our professor Lihua Xu, who provided us with academic supports, and our instructor Qingshun Wang, who have helped us to set up our project.



[^1]: I am Billy 1
[^2]: I am Ziyang Liao

