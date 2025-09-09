import './assets/main.css'
import "bootstrap/dist/css/bootstrap.min.css"
import "bootstrap"

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import App from './App.vue'
import router from './router'

const i18n = createI18n({
    locale: 'fi',
    fallbackLocale: 'en',
    messages: {
      fi: {
        message: {
          suodatin: 'Suodattimet',
          haku_painike: 'Hae',
          placeholder: 'Hakusana',
          yksikko: 'Yksikkö',
          huone: 'Huone',
          vastuuhenkilo: 'Vastuuhenkilö',
          tilanne: 'Tilanne',
          uusi_laite: 'Lisää uusi laite',
          tiedot_uusi: 'Lisää uuden laitteen tiedot',
          tay: 'TAY numero',
          tuotenimi: 'Tuotenimi',
          merkki: 'Merkki ja malli',
          sarjanumero: 'Sarjanumero',
          kampus: 'Kampus',
          rakennus: 'Rakennus',
          pvm: 'Toimituspäivämäärä',
          toimittaja: 'Toimittaja',
          lisatieto: 'Lisätieto',
          huoltosopimus_loppuu: 'Huoltosopimus loppuu',
          seuraava_huolto: 'Seuraava huolto',
          tallenna: 'Tallenna',
          tiedot_nykyinen: 'Laitteen tiedot',
          poista: 'Poista',
          paivita: 'Päivitä',
          poisto_teksti: 'Oletko varma, että haluat poistaa laitteen?',
          kylla_poisto: 'Kyllä, olen varma',
          peruuta: 'Peruuta',
          kotisivu: 'Kotisivu',
          kayttajasivu: 'Käyttäjät',
          tietoja: 'Tietoja',
          edellinen: 'Edellinen',
          seuraava: 'Seuraava',
          poistettu: "poistettu",
          muokkaa: "Muokkaa",
          onPaivitettu: "Tiedot päivitetty",
          lisattu: "on lisätty",
          kirjaudu_painike: "Kirjaudu",
          kirjaudu: "Kirjaudu sisään",
          sahkoposti: "Sähköposti",
          salasana: "Salasana",
          adminteksti: "Käyttöoikeuksien hallinta",
          admin_ei_oikeuksia: "Sinulla ei ole oikeuksia tähän näkymään",
          luo_kayttajakoodi: "Luo käyttäjäkoodi",
          kayttajakoodin_luonti: "Käyttäjäkoodin luonti",
          luo_uusi_kayttajakoodi: "Luo uusi koodi",
          luotu_kayttajakoodi: "Luotu käyttäjäkoodi",
          register_painike: "Rekisteröidy",
          koodi: "Kutsukoodi",
          koko_nimi: "Koko nimi",
          huoltosivu: "Huoltosopimukset",
          huoltoteksti: "Huoltoa odottavat laitteet",
          adminsivu: "Hallinta",
          adminteksti: "Käyttöoikeuksien hallinta",
          edellinen_huolto: "Edellinen huolto",
          seuraava_huolto: "Seuraava huolto",
          huoltosopimus_loppuu: "Huoltosopimuksen loppu"
        },
        tableHeaders: [
          "Tuotenimi",
          "Merkki ja malli",
          "Yksikkö",
          "Kampus",
          "Rakennus",
          "Huone",
          "Vastuuhenkilö",
          "Tilanne"
        ],
        userTableHeaders: [
          "Käyttäjätunnus",
          "Sähköposti"
        ],
        contractHeaders: [
          "Tuotenimi",
          "Seuraava huolto",
          "Edellinen huolto",
          "Vastuuhenkilö",
          "Huoltosopimus loppuu"
        ],
        fullHeaders: [
          "ID",
          "TAY numero",
          "Tuotenimi",
          "Merkki ja malli",
          "Sarjanumero",
          "Yksikkö",
          "Kampus",
          "Rakennus",
          "Huone",
          "Vastuuhenkilö",
          "Toimitus pvm",
          "Toimittaja",
          "Lisätieto",
          "Vanha sijainti",
          "Tarkistettu",
          "Huoltosopimus loppuu",
          "Edellinen huolto",
          "Seuraava huolto",
          "Tilanne"
        ]
      },
      en: {
        message: {
          suodatin: 'Filters',
          haku_painike: 'Search',
          placeholder: 'Search term',
          yksikko: 'Unit',
          huone: 'Room',
          vastuuhenkilo: 'Person in charge',
          tilanne: 'Status',
          uusi_laite: 'Add a new instrument',
          tiedot_uusi: 'Add new instrument information',
          tay: 'TAY number',
          tuotenimi: 'Product name',
          merkki: 'Make and model',
          sarjanumero: 'Serialnumber',
          kampus: 'Campus',
          rakennus: 'Building',
          pvm: 'Delivery date',
          toimittaja: 'Supplier',
          lisatieto: 'Further details',
          huoltosopimus_loppuu: 'Maintenance contract ends',
          seuraava_huolto: 'Next maintenance',
          tallenna: 'Save',
          tiedot_nykyinen: 'Instrument information',
          poista: 'Delete',
          paivita: 'Update',
          poisto_teksti: 'Are you sure you want to delete the instrument?',
          kylla_poisto: 'Yes, I am sure',
          peruuta: 'Cancel',
          kotisivu: 'Home',
          kayttajasivu: 'Users',
          tietoja: 'About',
          edellinen: 'Previous',
          seuraava: 'Next',
          poistettu: "deleted",
          muokkaa: "Edit",
          onPaivitettu: "Information has been updated",
          lisattu: "has been added",
          kirjaudu_painike: "Sign in",
          register_painike: "Register",
          kirjaudu: "Sign in",
          sahkoposti: "Email address",
          salasana: "Password",
          adminteksti: "Access control",
          admin_ei_oikeuksia: "You do not have permission to this view",
          luo_kayttajakoodi: "Generate user code",
          kayttajakoodin_luonti: "User code generation",
          luo_uusi_kayttajakoodi: "Generate new code",
          luotu_kayttajakoodi: "Generated user code",
          koodi: "Invite code",
          koko_nimi: "Full name",
          huoltosivu: "Maintenance contracts",
          huoltoteksti: "Instruments waiting for maintenance ",
          adminsivu: "Admin",
          adminteksti: "Access control",
          edellinen_huolto: "Previous maintenance",
          seuraava_huolto: "Next maintenance",
          huoltosopimus_loppuu: "End of the maintenance contract"
        },
        tableHeaders: [
          "Product Name",
          "Brand and Model",
          "Unit",
          "Campus",
          "Building",
          "Room",
          "Person in charge",
          "Status"
        ],
        userTableHeaders: [
          "Username",
          "Email",
        ],
        contractHeaders: [
          "Product Name",
          "Next maintenance",
          "Previous maintenance",
          "Maintenance contract ends",
          "Person in charge"
        ],
        fullHeaders: [
          "ID",
          "TAY number",
          "Product name",
          "Brand and Model",
          "Serial number",
          "Unit",
          "Campus",
          "Building",
          "Room",
          "Person in charge",
          "Delivery date",
          "Supplier",
          "Extra information",
          "Old location",
          "Last checked",
          "Maintenance contract ends",
          "Previous maintenance",
          "Next maintenance",
          "Status"
        ]
      },
    },
  });




const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')
