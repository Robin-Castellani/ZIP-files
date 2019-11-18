# *-* coding: utf-8 *-*

"""
Script che zippa i file contenuti in una cartella che hanno la data di
modifica compresa tra due date; la distanza tra le date usualmente è
pari ad 1 mese

Bisogna impostare manualmente il nome dell'impianto, la cartella con
i dati grezzi e la cartella dove salvare i dati zippati;
il formato di salvataggio dei dati .zip è:
    nome_impianto__data_iniziale__data_finale.zip

Lo script NON elimina i file dalla cartella dei dati grezzi.
"""

from __future__ import print_function
import os
import zipfile
from glob import glob
from dateutil.relativedelta import relativedelta
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
        print('{} già presente'. format(zip_name))
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


# ---------------------------

mongodb_psw, FIRST_DATE, LAST_DATE = parse_psw_begin_end_dates()

# delta di tempo
TIME_DELTA = relativedelta(months=1)

correzione_fuso_orario = datetime.timedelta(hours=2)

plants_documents = connect_to_db(mongodb_psw)

# ciclo su tutti gli impianti
for document in plants_documents:

    # cartella contenente i file da zippare
    folder = document[u'dati_grezzi_path']
    os.chdir(folder)
    # cartella dove i file zippati saranno spostati
    dest_folder = document[u'dati_grezzi_zipped_path']
    # nome dell'impianto
    nome_impianto = document[u'nome_impianto']

    print('\n\n\n' + nome_impianto + '\n------------')

    # dizionario contenente la lista dei file da zippare per ogni timedelta
    to_zip_all = dict()
    to_zip_timedelta = list()

    # data iniziale
    start_date = FIRST_DATE
    end_date = start_date + TIME_DELTA

    # ciclo per raccogliere tutti i file contenuti in ogni TIME_DELTA
    while start_date < LAST_DATE:

        for file_csv in glob('{}\*.csv'.format(folder)):

            data_file = (convert_date(os.path.getmtime(file_csv))
                         + correzione_fuso_orario)
    #        print(data_file)
    #        print(end_date)

            if start_date <= data_file < end_date:
                # print(file_csv)
                # print(data_file)
                to_zip_timedelta.append(file_csv)

        # salvataggio della lista dei file da zippare per tale mese
        to_zip_all['{}__{}'.format(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'))
            ] = to_zip_timedelta

        # aggiornamento della data di partenza
        print('{} - {} dati acquisiti, {} elementi'
              .format(start_date, end_date, len(to_zip_timedelta)))

        # reinizializzazione lista file da zippare nel timedelta
        to_zip_timedelta = list()

        # aggiornamento delle date
        start_date = end_date
        end_date += TIME_DELTA

    print('Oltre la data ultima')
    print('\n'.join(['Start: {}'.format(start_date),
                     'End: {}'.format(LAST_DATE)]))

    # zippaggio dei files
    for date, lista_to_zip in to_zip_all.iteritems():

        zip_name = zip_files(lista_to_zip, nome_impianto, date, dest_folder)

        # skips if no new file was created
        if not zip_name:
            continue

        # check che tutti i file zippati siano quelli effettivamente da zippare
        with zipfile.ZipFile(os.path.join(dest_folder, zip_name), 'r') as zipobj:
            files = zipobj.namelist()
            # creo ottengo i nomi (basename) di tutti i file da zippare
            lista_to_zip = [os.path.basename(file_) for file_ in lista_to_zip]
            # check che tutti i file siano presenti
            files_in_zip = [file_ in lista_to_zip for file_ in files]
            # ottengo lo stato complessivo di presenza dei file
            copy_in_zip_ok = all(files_in_zip)

        # assert every file has been copied in the zip file
        assert(copy_in_zip_ok is True)

        for file_to_delete in lista_to_zip:
            os.remove(file_to_delete)

    '''
    # informazioni per ogni file contenente in ogni file .zip
    for file_name in glob('{}\*.zip'.format(dest_folder)):
        with zipfile.zipfile(file_name, 'r') as zip:
            for info in zip.infolist():
                print(info.filename)
                print('\tmodified:\t' + str(datetime.datetime(*info.date_time)))
                print('\tsystem:\t\t' + str(info.create_system) +
                      '(0 = windows, 3 = unix)')
                print('\tzip version:\t' + str(info.create_version))
                print('\tcompressed:\t' + str(info.compress_size) + ' bytes')
                print('\tUncompressed:\t' + str(info.file_size) + ' bytes')
    '''