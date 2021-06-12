from .Database import Database


class DataRepository:
    @staticmethod
    def json_or_formdata(request):
        if request.content_type == 'application/json':
            gegevens = request.get_json()
        else:
            gegevens = request.form.to_dict()
        return gegevens

    # read
    # history
    @staticmethod
    def read_last_data(installatie_id, sensor_actuatorid):
        sql = "SELECT Sensor_ActuatorId, Waarde FROM optimalgrowdb.historiek where InstallatieId = %s and Sensor_ActuatorId = %s order by DatumTijd desc limit 1"
        params = [installatie_id, sensor_actuatorid]
        return Database.get_one_row(sql, params)

    @staticmethod
    def read_history_of_sensorid(installatie_id, sensor_actuatorid):
        sql = "SELECT Sensor_ActuatorId, concat(datumtijd) as Datumtijd, Waarde FROM optimalgrowdb.historiek where InstallatieId = %s and Sensor_ActuatorId = %s order by DatumTijd desc limit 100"
        params = [installatie_id, sensor_actuatorid]
        return Database.get_rows(sql, params)

    # installatie
    @staticmethod
    def read_installation_data(installatie_id):
        sql = "SELECT * FROM installatie WHERE Id = %s"
        params = [installatie_id]
        return Database.get_one_row(sql, params)

    # insert
    @staticmethod
    def add_log(installatie_id, sensor_actuatorid, waarde):
        sql = "INSERT INTO historiek (installatieId, sensor_actuatorId, waarde) VALUES (%s, %s, %s);"
        params = [installatie_id, sensor_actuatorid, waarde]
        return Database.execute_sql(sql, params)

    # update
    @staticmethod
    def Update_installatie(installatie_id, Naam, Spaarstand,  LichtDrempel, WaterDrempel):
        sql = "UPDATE installatie SET Naam = %s, Spaarstand = %s, LichtDrempel = %s, WaterDrempel = %s WHERE Id = %s;"
        params = [Naam, Spaarstand, LichtDrempel, WaterDrempel, installatie_id]
        return Database.execute_sql(sql, params)
