# ZIP files a cadenza mensile in un cartella via CLI

Lo script crea un file `.zip` nella `destination_folder` di tutti i file
presenti nella `origin_folder`; i file vengono raggruppati su base mensile
in base alla loro data di modifica.
Il nome dei file è del tipo:

`nome_impianto__data_iniziale__data_finale.zip`

dove `nome_impianto` è il primo parametro dato in input.

L'utilizzo è il seguente:
`python Zip_files.py nome_impianto origin_folder destination_folder`

Lo script **non** cancella i file che vengono zippati.
