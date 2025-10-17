<script setup>
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

</script>

<template>
  <div class="content">
    <h3 class="mb-4">{{ t('message.instrumenttitietojen_tuonti_vienti') }}</h3>
    <div class="row g-4">
      <!-- Import Card -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h4 class="card-title mb-3">{{ t('message.tuo_tiedot') }}</h4>
            <p class="card-text mb-4">
              {{ t('message.tuo_tiedot_kuvaus') }}
              <br>
              {{ t('message.tuo_tiedot_kuvaus_lisa') }}
            </p>
            <div class="d-grid gap-2">
              <button class="btn btn-outline-primary">
                {{ t('message.lataa_mallipohja') }}
              </button>
              <button class="btn btn-outline-primary">
                {{ t('message.valitse_tiedosto') }}
              </button>
              <!-- TODO: undisable once file has been selected -->
              <button class="btn btn-primary" disabled>
                {{ t('message.tuo_tiedot_nappi') }}
              </button>
            </div>
            <!-- TODO: Something like this to show success after data transfer
            <div class="mt-3 text-success">
              <small>{{ t('message.tiedot_tuotu_onnistuneesti', { count: 3123 }) }}</small>
            </div>
            -->
          </div>
        </div>
      </div>

      <!-- Export Card -->
      <!-- TODO: SHOW CONFIRMATION MODAL ON EXPORT -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-body">
            <h4 class="card-title mb-3">{{ t('message.vie_tiedot') }}</h4>
            <p class="card-text mb-4">
              {{ t('message.vie_tiedot_kuvaus') }}
            </p>
            <div class="d-grid gap-2">
              <button class="btn btn-primary">
                {{ t('message.vie_instrumenttirekisteri') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.content {
  padding-bottom: 88px;
}

.card {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: box-shadow 0.3s ease;
}

.card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.card-title {
  color: #4E008E;
  font-weight: 600;
}
</style>

