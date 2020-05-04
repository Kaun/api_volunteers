import csv
import os


from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "randomstring"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///volunteer.db"
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

current_path = os.path.dirname(os.path.realpath(__file__))


# event_location_association = db.Table('event_location',
#                                   db.Column('event_id', db.Integer, db.ForeignKey('events.id')),
#                                   db.Column('location_id', db.Integer, db.ForeignKey('locations.id')))


class District(db.Model):
    __tablename__ = 'districts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    streets = db.relationship('Street', back_populates='district')


class Street(db.Model):
    __tablename__ = 'streets'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"))
    district = db.relationship('District', back_populates="streets")


with app.app_context():
    db.create_all()

    with open(os.path.join(current_path, 'districts.csv'), encoding='utf-8') as csvfile_districts:
        reader = csv.DictReader(csvfile_districts)
        data_districts = [row for row in reader]
    db_check_districts = db.session.query(District).get(1)
    if db_check_districts is None:
        for row in data_districts:
            district = District(title=row['title'])
            db.session.add(district)

    with open(os.path.join(current_path, 'streets.csv'), encoding='utf-8') as csvfile_streets:
        reader = csv.DictReader(csvfile_streets)
        data_streets = [row for row in reader]
    db_check_streets = db.session.query(Street).get(1)
    if db_check_streets is None:
        for row in data_streets:
            district = row['district']
            street = Street(title=row['title'], district_id=district)
            db.session.add(street)
    db.session.commit()


@app.route('/districts', methods=['GET'])
def api_districts_list():
    districts = db.session.query(District)
    district_dict = []

    for district in districts:
        district_dict.append(dict(title=district.title))
        # district_dict.append(district.title)

    # jsonify(district_dict)
    # return f'{district_dict}'
    return jsonify(district_dict)

@app.route('/streets', methods=['GET'])
def api_streets_list():
    id_district = request.args.get('district')
    if id_district:
        streets = db.session.query(Street).filter(Street.district_id == id_district)
    streets_dict = []
    for street in streets:
        streets_dict.append(dict(street=street.title, id_district=street.district_id ))
    return jsonify(streets_dict), 404


if __name__ == '__main__':
    app.run()
