# *-* coding: utf-8 *-*

"""
Script che zippa i file contenuti in una cartella che hanno la data di
modifica compresa tra due date; la distanza tra le date usualmente è
pari ad 1 mese

Bisogna impostare manualmente il nome dell'impianto, la cartella con
i dati grezzi e la cartella dove salvare i dati zippati;
il formato di salvataggio dei dati .zip è:
    nome_impianto__data_iniziale__data_finale.zip

Lo script elimina i file dalla cartella dei dati grezzi.
"""

from __future__ import print_function
from glob import glob
from dateutil.relativedelta import relativedelta
from functions import *


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

        for file_csv in glob('{}\\*.csv'.format(folder)):

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
    for date, lista_to_zip in to_zip_all.items():

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
