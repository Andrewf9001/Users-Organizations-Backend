from flask import request, Flask, jsonify, Response

import psycopg2

app = Flask(__name__)

conn = psycopg2.connect("dbname='crm' user='andrewfletcher' host='localhost'")
cursor = conn.cursor()

def create_all():
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
      user_id SERIAL PRIMARY KEY,
      first_name VARCHAR NOT NULL,
      last_name VARCHAR,
      email VARCHAR NOT NULL UNIQUE,
      phone VARCHAR,
      city VARCHAR,
      state VARCHAR,
      org_id INT,
      active SMALLINT
    );
  """)

  cursor.execute("""
    CREATE TABLE IF NOT EXISTS Organizations (
      org_id SERIAL PRIMARY KEY,
      name VARCHAR NOT NULL,
      phone VARCHAR,
      city VARCHAR,
      state VARCHAR,
      active SMALLINT
    );
  """)
  conn.commit()

  cursor.execute("SELECT org_id FROM Organizations WHERE name='DevPipeline';")
  results = cursor.fetchone()
  org_id = -999

  if not results:
    cursor.execute("""
      INSERT INTO Organizations
        (name, phone, city, state, active)
        VALUES('DevPipeline', '3853090807', 'Orem', 'UT', 1)
      RETURNING org_id;
    """)
    org_id = cursor.fetchone()[0]
    conn.commit()

  cursor.execute("SELECT * FROM Users WHERE email='admin@devpipeline.com'")
  results = cursor.fetchone()

  if not results:
    cursor.execute("""
      INSERT INTO Users
        (first_name, last_name, email, phone, city, state, org_id, active)
        VALUES('Admin', 'Admin', 'admin@devpipeline.com', '8088088088', 'SLC', 'UT', 1, 1);
    """)
    conn.commit()


@app.route('/users', methods=['GET'])
def get_all_users():
  output_json = {}
  results_json = []

  cursor.execute("""
    SELECT 
      u.user_id, u.first_name, u.last_name, u.email,
      u.phone, u.city, u.state, u.org_id, u.active,
      o.org_id, o.name, o.city, o.state, o.active
    FROM Users u
    JOIN Organizations o
      ON
        o.org_id = u.org_id;
  """)

  results = cursor.fetchall()

  for user in results:
    new_record = {
      "user_id": user[0],
      "first_name": user[1],
      "last_name": user[2],
      "email": user[3],
      "phone": user[4],
      "city": user[5],
      "state": user[6],
      "active": user[7],
      "organizations": {
        "active": user[13],
        "name": user[10]
      }
    }

    results_json.append(new_record)

  output_json = { "results": results_json }

  return jsonify(output_json), 200


@app.route("/user/add", methods=["POST"])
def add_user():
  form = request.form
  fields = ['first_name', 'last_name', 'email', 'phone', 'city', 'state', 'active']
  required_fields = ['first_name', 'email']
  values = []

  for field in fields:
    form_value = form.get(field)

    if form_value in required_fields and form_value == '':
      return jsonify(f'{field} is required!'), 400

    values.append(form_value)

  cursor.execute("""
    INSERT INTO Users (first_name, last_name, email, phone, city, state, active) 
    VALUES (%s, %s, %s, %s, %s, %s, %s);
  """, values)

  conn.commit()

  return jsonify("User Added"), 200


@app.route('/organizations', methods=['GET'])
def get_all_organizations():
  output_json = {}
  results_json = []

  cursor.execute("""
    SELECT 
      org_id, name, phone, city, state, active
    FROM Organizations;
  """)

  results = cursor.fetchall()

  for user in results:
    new_record = {
      "org_id": user[0],
      "name": user[1],
      "phone": user[2],
      "city": user[3],
      "state": user[4],
      "active": user[5]
    }

    results_json.append(new_record)

  output_json = { "results": results_json }

  return jsonify(output_json), 200


@app.route('/organization/<org_id>', methods=['GET'])
def get_single_organizations(org_id):
  output_json = {}
  results_json = []

  cursor.execute("""
    SELECT 
      org_id, name, phone, city, state, active
    FROM Organizations
    WHERE org_id = %s;
  """, [org_id, ])

  org_results = cursor.fetchone()

  if org_results is None:
    return jsonify("No Organization Found"), 404
  else:
    new_record = {
      "org_id": org_results[0],
      "name": org_results[1],
      "phone": org_results[2],
      "city": org_results[3],
      "state": org_results[4],
      "active": org_results[5]
    }

    results_json.append(new_record)
    output_json = { "results": results_json }

    return jsonify(output_json), 200


@app.route("/organization/add", methods=["POST"])
def add_organization():
  form = request.form
  fields = ['name', 'phone', 'city', 'state', 'active']
  required_fields = ['name']
  values = []

  for field in fields:
    form_value = form.get(field)

    if form_value in required_fields and form_value == '':
      return jsonify(f'{field} is required!'), 400

    values.append(form_value)

  cursor.execute("""
    INSERT INTO Organizations (name, phone, city, state, active) 
    VALUES (%s, %s, %s, %s, %s);
  """, values)

  conn.commit()

  return jsonify("Organization Added"), 200


@app.route("/organization/edit/<org_id>", methods=["PUT"])
def edit_organization(org_id):
  cursor.execute("SELECT org_id, name, phone, city, state, active FROM Organizations WHERE org_id = %s", [org_id, ])
  results = cursor.fetchone()

  if results == None:
    return jsonify("No Organization Found"), 404
  else:
    org_form = request.form
    name = org_form.get('name')
    phone = org_form.get('phone')
    city = org_form.get('city')
    state = org_form.get('state')
    active = org_form.get('active')

    if name == '':
      name = results[1]

    if phone == '':
      phone = results[2]

    if city == '':
      city = results[3]

    if state == '':
      state = results[4]

    if active == '':
      active = results[5]

    cursor.execute("""
      UPDATE Organizations SET name = %s, phone = %s, city = %s, state = %s, active = %s WHERE org_id = %s
    """, [name, phone, city, state, active, org_id])

    conn.commit()

    return jsonify("Edited Organization"), 200


@app.route('/organization/delete/<org_id>', methods=['DELETE'])
def delete_organization(org_id):
  cursor.execute("SELECT org_id, name FROM Organizations WHERE org_id = %s", [org_id, ])
  query_results = cursor.fetchone()

  if query_results == None:
    return jsonify("No Organization Found"), 404
  else:
    cursor.execute("DELETE FROM Organizations WHERE org_id = %s", [org_id,])

    conn.commit()

    return jsonify(f"Organization: {query_results[1]}, Record Deleted"), 200


if __name__ == '__main__':
  create_all()
  app.run()