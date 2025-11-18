from django.core.management import call_command
from django.core.management import CommandError
from django.test import TestCase
from datetime import date, datetime
import os

class TestImport(TestCase):

    invalid_data_path = "invalid_data.csv"
    valid_data_path = "valid_data.csv"

    @classmethod
    def setUpTestData(cls):
        invalid_csv = "hahaha;;;dsadcxz\nfdasfasdf;fdasf;fdsa"
        valid_csv = "tay_numero;tuotenimi;merkki_ja_malli;sarjanumero;yksikko;kampus;rakennus;huone;vastuuhenkilo;toimituspvm;toimittaja;lisatieto;vanha_sijainti;tarkistettu;tilanne\n27438;valaisin;Philips Origina;-;Kirjasto yhteiset;Kauppi;Arvo;ARVO-B008;;2025-01-15;Instrumentarium;;;;Tarkistamatta"

        with open(cls.invalid_data_path, mode="w", encoding="utf-8") as f:
            f.write(invalid_csv)
        
        with open(cls.valid_data_path, mode="w", encoding="utf-8") as f:
            f.write(valid_csv)
    
    @classmethod
    def tearDownClass(cls):
        super(TestImport, cls).tearDownClass()
        os.remove(cls.invalid_data_path)
        os.remove(cls.valid_data_path)
        

    def test_import_no_file(self):
        args = []
        opts = {}
        try:
            call_command("import_csv", *args, **opts)
        except CommandError as e:
            self.assertEqual(e.args, ('Error: the following arguments are required: csv_path',))
            return

        self.fail()

    def test_import_invalid_path(self):
        args = ["grhghesrgzerzgszefhgzlgf"]
        opts = {}
        try:
            call_command("import_csv", *args, **opts)
        except FileNotFoundError:
            return

        self.fail()

    def test_import_invalid_file(self):
        args = [self.invalid_data_path]
        opts = {}
        try:
            call_command("import_csv", *args, **opts)
        except Exception:
            # Expected to fail due to invalid CSV format
            return

        self.fail()
    
    def test_import_valid_file(self):
        args = [self.valid_data_path]
        opts = {}
        # Should not raise any exception
        call_command("import_csv", *args, **opts)

class TestExport(TestCase):

    import_path = "import.csv"
    csv_data = "tay_numero;tuotenimi;merkki_ja_malli;sarjanumero;yksikko;kampus;rakennus;huone;vastuuhenkilo;toimituspvm;toimittaja;lisatieto;vanha_sijainti;tarkistettu;tilanne\n27438;valaisin;Philips Origina;-;Kirjasto yhteiset;Kauppi;Arvo;ARVO-B008;;2025-01-15;Instrumentarium;;;;Tarkistamatta"
    

    @classmethod
    def setUpTestData(cls):
        with open(cls.import_path, mode="w", encoding="utf-8") as f:
            f.write(cls.csv_data)

        args = [cls.import_path]
        opts = {}
        
        call_command("import_csv", *args, **opts)

    def test_export(self):
        args = []
        opts = {}

        call_command("export_csv", *args, **opts)

        current_date_string = datetime.now().strftime("%G-%m-%d")

        for file in os.listdir():
            if file.startswith("laiterekisteri_"):
                if current_date_string in file:
                    os.remove(file)
                    return

        self.fail()

    @classmethod
    def tearDownClass(cls):
        super(TestExport, cls).tearDownClass()
        os.remove(cls.import_path)
        