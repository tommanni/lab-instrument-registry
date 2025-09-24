<script setup>
import axios from 'axios'
import { ref } from 'vue'
import { useDataStore } from '@/stores/data'
import { useAlertStore } from '@/stores/alert'
import { useI18n } from 'vue-i18n';

const i18n = useI18n();
const store = useDataStore()
const showOverlay = ref(false)
const alertStore = useAlertStore()

// Factory function to create base form data (core instrument fields only)
// Funktio, joka luo peruslomakedata (vain ydinlaitteen kentät)
const createBaseFormData = () => ({
  tay_numero: '',
  tuotenimi: '',
  merkki_ja_malli: '',
  sarjanumero: '',
  yksikko: '',
  kampus: '',
  rakennus: '',
  huone: '',
  vastuuhenkilo: '',
  toimituspvm: '',
  toimittaja: '',
  lisatieto: '',
  tilanne: "Saatavilla"
})

// Factory function to create form data with maintenance fields for reset
// Funktio, joka luo lomakedata huoltokentillä nollausta varten
const createFormDataWithMaintenance = () => ({
  ...createBaseFormData(),
  huoltosopimus_loppuu: '',
  edellinen_huolto: '',
  seuraava_huolto: ''
})

// Lomakedata, joka tallennetaan
// Form data that will be saved
const formData = ref(createBaseFormData())

const openOverlay = () => {
  showOverlay.value = true
}

const closeOverlay = () => {
  showOverlay.value = false
}

const emptyForm = () => {
  formData.value = createFormDataWithMaintenance()
}

const saveData = async () => {
  console.log(JSON.parse(JSON.stringify(formData.value)))
  /*
    attempt to save the instrument
    alert the user whether it succeeded
  */
  try {
    const headers = {
      "Authorization":  'Token ' + document.cookie.split("; ").find((row) => row.startsWith("Authorization="))?.split("=")[1]
    }
    // send the data without any empty fields
    var dataToSend = {};
    for (const key in formData.value) {
      if (formData.value[key] !== "") {
        dataToSend[key] = formData.value[key]
      }
    }

    await axios.post('/api/instruments/', dataToSend, {headers: headers})

    alertStore.showAlert(0, `${dataToSend.tuotenimi} ${i18n.t('message.lisattu')}`)
    store.addObject(formData.value)
    // todo sometimes the instrument doesn't appear in the list or otherwise breaks it
    // doesn't make any sense why

  }
  catch (e) {
    alertStore.showAlert(1, `${formData.value.tuotenimi} ${i18n.t('message.ei_lisattu')}: ${e}`)
  }

  emptyForm()
  closeOverlay()
  }
</script>


<template>
    <div>
      <!-- Avausnappi -->
      <!-- Open button -->
      <button v-if="store.isLoggedIn" class="add-button" @click="openOverlay">{{$t('message.uusi_laite')}}</button>
  
      <!-- Overlay näkyy vain, kun showOverlay on true -->
      <!-- Overlay is visible on when showOverlay is true -->
      <div v-if="showOverlay" class="overlay-backdrop">
        <div class="overlay-content">
          <!-- X-painike oikeassa yläkulmassa -->
          <!-- X button in upper right corner -->
          <button class="close-button" @click="closeOverlay">×</button>
          
          <h3>{{$t('message.tiedot_uusi')}}</h3>
          <p></p>
          <div @submit.prevent="validateForm" class="two-col-form needs-validation"  novalidate>
             <div class="col">
                <label for="tuotenimi">{{$t('message.tuotenimi')}}</label>
                <input id="tuotenimi" v-model="formData.tuotenimi" />

                <label for="sarjanumero">{{$t('message.sarjanumero')}}</label>
                <input id="sarjanumero" v-model="formData.sarjanumero" />

                <label for="kampus">{{$t('message.kampus')}}</label>
                <input id="kampus" v-model="formData.kampus" />

                <label for="huone">{{$t('message.huone')}}</label>
                <input id="huone" v-model="formData.huone" placeholder="ARVO-D007" />

                <label for="toimituspvm">{{$t('message.pvm')}}</label>
                <input 
                  id="toimituspvm"
                  v-model="formData.toimituspvm"
                  type="date"
                  class="form-control"
                  required
                />

                <label for="lisatieto">{{$t('message.lisatieto')}}</label>
                <input id="lisatieto" v-model="formData.lisatieto" />

                <label for="huoltosopimus_loppuu">{{ $t('message.huoltosopimus_loppuu') }}</label>
                <input id="huoltosopimus_loppuu" v-model="formData.huoltosopimus_loppuu" type="date"/>

             </div>

              <div class="col">
                <label for="tay_numero">{{$t('message.tay')}}</label>
                <input id="tay_numero" v-model="formData.tay_numero" placeholder="12345" />

                <label for="merkki_ja_malli">{{$t('message.merkki')}}</label>
                <input id="merkki_ja_mali" v-model="formData.merkki_ja_malli" />

                <label for="yksikko">{{$t('message.yksikko')}}</label>
                <input id="yksikko" v-model="formData.yksikko" />

                <label for="rakennus">{{$t('message.rakennus')}}</label>
                <input id="rakennus" v-model="formData.rakennus" />
              
                <label for="vastuuhenkilo">{{$t('message.vastuuhenkilo')}}</label>
                <input id="vastuuhenkilo" v-model="formData.vastuuhenkilo" />

                <label for="toimittaja">{{$t('message.toimittaja')}}</label>
                <input id="toimittaja" v-model="formData.toimittaja" />

                <label for="edellinen_huolto">{{ $t('message.edellinen_huolto') }}</label>
                <input id="edellinen_huolto" v-model="formData.edellinen_huolto" type="date" />

                <label for="seuraava_huolto">{{ $t('message.seuraava_huolto') }}</label>
                <input id="seuraava_huolto" v-model="formData.seuraava_huolto" type="date"/>

              </div>
          </div>
          <br/>
          <button class="save-button" @click="saveData">{{$t('message.tallenna')}}</button>

        </div>
      </div>
    </div>
</template>
  
<style scoped>
/* Puoliläpinäkyvä tausta overlaylle */
/* Semi transparent background for overlay */
.overlay-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1031;
}

/* Keskitetty sisältö overlayn sisällä */
/* Centered content inside the overlay */
.overlay-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #fff;
  padding: 2em;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.add-button {
  padding: 5px 10px;  /* Keep padding controlled */
  margin-left: 10px;
  background-color: #cf286f;
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  text-align: center;
  white-space: nowrap;
}

/* Tyylit aktiiviselle hover-tilalle */
/* Styles for the active hover mode */
.add-button:hover {
  background-color: #F5A5C8; /* hieman tummempi sävy hoverissa / slighly darkder shade while hovering*/
}

/* X-painike overlayn yläkulmassa */
/* X button in the upper corner of the overlay */
.close-button {
  position: absolute;
  top: 0.5em;
  right: 0.5em;
  background: transparent;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  line-height: 1;
}

.close-button:hover {
  color: #b00; /* Vaihda hoverin väri tarpeen mukaan / change the hover color if needed*/
}
/* Kaksi saraketta vierekkäin */
/* Two columns side by side */
.two-col-form {
  display: flex;
  gap: 1em;
}

.col {
  display: flex;
  flex-direction: column;
  gap: 0.5em; /* pieni väli kenttien välillä / small gap between fields*/
}

.save-button {
  padding: 5px 10px;  /* Keep padding controlled */
  background-color: rgb(0, 150, 0);
  color: white;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  text-align: center;
  white-space: nowrap;
}

.save-button:hover {
  background-color: rgb(0, 234, 0); /* hieman tummempi sävy hoverissa / slighly darker shade when hovering*/
}

</style>