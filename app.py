import csv
import os
import json


from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "randomstring"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///volunteer.db"
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

current_path = os.path.dirname(os.path.realpath(__file__))


volunteer_street_association = db.Table('volunteer_street',
                                  db.Column('volunteer_id', db.Integer, db.ForeignKey('volunteers.id')),
                                  db.Column('street_id', db.Integer, db.ForeignKey('streets.id')))


class District(db.Model):
    __tablename__ = 'districts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    streets = db.relationship('Street', back_populates='district')


class Street(db.Model):
    __tablename__ = 'streets'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    volunteer = db.relationship('Volunteer', secondary=volunteer_street_association, back_populates="streets")
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"))
    district = db.relationship('District', back_populates="streets")


class Volunteer(db.Model):
    __tablename__ = 'volunteers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    userpic = db.Column(db.String)
    phone = db.Column(db.String)
    streets = db.relationship('Street', secondary=volunteer_street_association, back_populates="volunteer")


class Requisition(db.Model):
    __tablename__ = 'requestions'

    id = db.Column(db.Integer, primary_key=True)
    district = db.Column(db.Integer)
    street = db.Column(db.Integer)
    volunteer = db.Column(db.Integer)
    address = db.Column(db.String)
    name = db.Column(db.String)
    surname = db.Column(db.String)
    phone = db.Column(db.String)
    text = db.Column(db.String)


with app.app_context():
    db.create_all()

    with open(os.path.join(current_path, 'volunteers.json'), 'r', encoding='utf-8') as jsonfile_volunteers:
        volunteers = json.load(jsonfile_volunteers)

    db_check_volunteers = db.session.query(Volunteer).get(1)
    if db_check_volunteers is None:
        for id, volunteer_data in volunteers.items():
            volunteer = Volunteer(name=volunteer_data['name'], userpic=volunteer_data['userpic'],
                                  phone=volunteer_data['phone'])
            db.session.add(volunteer)

    with open(os.path.join(current_path, 'streets.json'), 'r', encoding='utf-8') as jsonfile_streets:
        streets = json.load(jsonfile_streets)

    db_check_streets = db.session.query(Street).get(1)
    if db_check_streets is None:
        for id, street_dict in streets.items():
            street = Street(title=street_dict['title'])
            for volunteer in street_dict['volunteer']:
                volunteer_db = db.session.query(Volunteer).get_or_404(volunteer)
                street.volunteer.append(volunteer_db)
            db.session.add(street)

    with open(os.path.join(current_path, 'districts.json'), 'r', encoding='utf-8') as jsonfile_districts:
        districts = json.load(jsonfile_districts)

    db_check_districts = db.session.query(District).get(1)
    if db_check_districts is None:
        for id, district_dict in districts.items():
            district = District(title=district_dict['title'])
            for street in district_dict['streets']:
                street_db = db.session.query(Street).get_or_404(street)
                district.streets.append(street_db)
            db.session.add(street_db)
    db.session.commit()


@app.route('/districts', methods=['GET'])
def api_districts_list():
    districts = db.session.query(District)

    district_dict = []
    for district in districts:
        district_dict.append(dict(id=district.id, title=district.title,))
    return jsonify(district_dict)

@app.route('/streets', methods=['GET'])
def api_streets_list():
    id_district = request.args.get('district')
    if id_district:
        streets = db.session.query(Street).filter(Street.district_id == id_district)

    streets_dict = []
    for street in streets:
        volunteers = [volunteer.id for volunteer in street.volunteer]
        streets_dict.append(dict(id=street.id, street=street.title, volunteer=volunteers))
    return jsonify(streets_dict), 404


@app.route('/volunteers', methods=['GET'])
def api_volunteers_list():
    id_street = request.args.get('streets')
    if id_street:
        street = db.session.query(Street).get_or_404(id_street)

    volunteers_dict = []
    for volunteer in street.volunteer:
        volunteers_dict.append(dict(id=volunteer.id, name=volunteer.name,
                                    userpic=volunteer.userpic, phone=volunteer.phone))
    return jsonify(volunteers_dict), 404


@app.route('/helpme', methods=['POST'])
def api_request():
    data = request.json

    requestion = Requisition(district=data.get('district'), street=data.get('street'), volunteer=data.get('volunteer'),
                             address=data.get('address'), name=data.get('name'), surname=data.get('surname'),
                             phone=data.get('phone'), text=data.get('text'))
    db.session.add(requestion)
    db.session.commit()
    return jsonify(status='success'), 201, {"Location": "/helpme/" + str(requestion.id)}


if __name__ == '__main__':
    app.run()
