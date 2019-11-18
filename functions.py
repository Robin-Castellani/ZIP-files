# coding=utf-8
import os
import zipfile
import datetime
import argparse
from pymongo import MongoClient


def parse_psw_begin_end_dates():
    """
    CLI to parse the MongoDB password, the begin date and the end date
    between which zip the files
    :return:
        the MongoDB password
        the begin date
        the end date
    """
    # get MongoDB password and date limits
    parser = argparse.ArgumentParser(
        description="Zip files dell'impianto; inserire password, data iniziale e finale")
    # definizione argomenti parser
    parser.add_argument(
        'Password', metavar='nome', type=str,
        help="Password di MongoDB")
    parser.add_argument(
        'Data_di_inizio', metavar='begin-date', type=str,
        help='Anno, mese e giorno da cui partire per il salvataggio dei dati')
    parser.add_argument(
        'Data_di_fine', metavar='end-date', type=str,
        help='Anno, mese e giorno in cui terminare il salvataggio dei dati')
    # esecuzione del parser
    args = parser.parse_args()

    # password
    mongodb_psw = args.Password
    # data iniziale
    data_iniziale = args.Data_di_inizio
    # data finale
    data_finale = args.Data_di_fine

    # momento iniziale e finale per cui si vuole zippare i file
    begin_date = datetime.datetime(
        int(data_iniziale[0:4]), int(data_iniziale[4:6]),
        int(data_iniziale[6:8]),
        00, 00, 00)

    end_date = datetime.datetime(
        int(data_finale[0:4]), int(data_finale[4:6]),
        int(data_finale[6:8]),
        23, 59, 59)

    return mongodb_psw, begin_date, end_date


def connect_to_db(psw):
    """
    Connect to MongoDB
    :param psw:
        MongoDB password
    :return:
        document generator
    """

    # connection to MongoDB
    connection_string = str(
        'mongodb+srv://robin-c:{}'.format(psw) +
        '@info-scaricamento-dati-l4hzo.gcp.mongodb.net/test?retryWrites=true&w=majority'
    )
    db_name = 'dati-impianti'
    collection_name = 'dati-impianti'

    client = MongoClient(connection_string)
    collection = client[db_name][collection_name]

    print('Connesso al db {}\nCollezione {}\n- - - - - - -\n'
          .format(db_name, collection_name))

    return collection.find()


def convert_date(timestamp):
    """Converte la data di tipo timestamp in data da datetime
    Restituisce la data datetime
    """

    d = datetime.datetime.utcfromtimestamp(timestamp)
    return d


def zip_files(lista_to_zip, nome_impianto, date, dest_folder):
    """Funzione che zippa i files di un timedelta
    Effettua verifiche:
    è già presente lo stesso file?
    ci sono file da zippare?

    :returns zip_name
        name of the zip file
    """

    # zip dei files
    zip_name = '{}__{}.zip'.format(nome_impianto, date)
    print('Zippando {}'.format(zip_name))

    # nel caso in cui lo zip sia già presente, lo salta
    if zip_name in os.listdir(dest_folder):
        print('{} già presente'.format(zip_name))
        return ''

    # nel caso in cui non ci siano file da zippare
    if not lista_to_zip:
        print('Nessun file da zippare in {}'.format(zip_name))
        return ''

    with zipfile.ZipFile(os.path.join(dest_folder, zip_name), 'w',
                         compression=zipfile.ZIP_DEFLATED) as new_z:

        for file_to_zip in lista_to_zip:
            new_z.write(os.path.basename(file_to_zip))

        print('Zippaggio terminato {}'.format(date))
        print('------------')

    return zip_name
