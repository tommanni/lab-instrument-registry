<script>
import axios from 'axios';

// Define filters
export default {
  name: 'FilterComponent',

  data() {
    return {
      openDropdown: null,
      filters: []
    }
  },

  emits: ['filter-change'],

  created() {
    this.filters = [
      {
        name: this.$t('message.yksikko'),
        field: 'yksikko',
        options: [],
        selected: null,
        searchTerm: ''
      },
      {
        name: this.$t('message.huone'),
        field: 'huone',
        options: [],
        selected: null,
        searchTerm: ''
      },
      {
        name: this.$t('message.vastuuhenkilo'),
        field: 'vastuuhenkilo',
        options: [],
        selected: null,
        searchTerm: ''
      },
      {
        name: this.$t('message.tilanne'),
        field: 'tilanne',
        options: [],
        selected: null,
        searchTerm: ''
      }
    ]
  },

  mounted() {
    this.filters.forEach(filter => {
      const cookieName = this.getCookieName(filter.field);
      const savedValue = this.getCookie(cookieName);
      if (savedValue) {
        filter.selected = savedValue;
      }
      this.fetchFilterOptions(filter)
    })
  },

  methods: {
    async fetchFilterOptions(filter) {
      try {
        const res = await axios.get(`/api/instruments/valueset/${filter.field}/`, {
          withCredentials: true
        });

        filter.options = res.data.data.map(s => s.trim()).sort((a, b) => a ? b ? a.localeCompare(b) : -1 : 1) || []
      }
      catch (error) {
        // Error fetching filter option
      }
    },

    toggleDropdown(index) {
      this.openDropdown = (this.openDropdown === index) ? null : index
    },

    applyFilter(filterIndex, option) {
      this.filters[filterIndex].selected = option
      this.openDropdown = null

      this.$emit('filter-change', {
        filterName: this.filters[filterIndex].field,
        value: option
      })
    },

    getCookie(name) {
      const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
      return match ? decodeURIComponent(match[2]) : null;
    },

    getCookieName(field) {
      switch (field) {
        case 'yksikko': return 'YksikkoFilter';
        case 'huone': return 'HuoneFilter';
        case 'vastuuhenkilo': return 'VastuuHFilter';
        case 'tilanne': return 'TilanneFilter';
        default: return '';
      }
    },

    clearFilter(filterIndex) {
      const filter = this.filters[filterIndex];
      filter.selected = null;
      filter.searchTerm = ''

      const cookieName = this.getCookieName(filter.field);
      // TODO Add cookie flags for live build
      document.cookie = `${cookieName}=; Path=/; Max-Age=0` /*; Secure; SameSite=Strict*/

      this.$emit('filter-change', {
        filterName: filter.field,
        value: null
      })
    },
    filteredOptions(filter) {
      if (!filter.searchTerm) {
        return filter.options
      }

      const lowerTerm = filter.searchTerm.toLowerCase()
      return filter.options.filter(opt =>
        opt.toLowerCase().includes(lowerTerm)
      )
    },
    
    clearAllFilters() {
      const clearedFilters = {};

      this.filters.forEach(filter => {
        filter.selected = null;
        filter.searchTerm = ''

        const cookieName = this.getCookieName(filter.field);
        // TODO Add cookie flags for live build
        document.cookie = `${cookieName}=; Path=/; Max-Age=0` /*; Secure; SameSite=Strict*/

        clearedFilters[filter.field] = null;
      });

      this.openDropdown = null;

      this.$emit('all-filters-cleared', clearedFilters);
    }
  },

}
</script>

<template>
  <ul class="filter-wrapper gap-3 ms-md-2">
    <li class="filter-slot" v-for="(filter, index) in filters" :key="index">
      <div class="dropdown">
        <button class="btn border dropdown-toggle d-toggle rounded" type="button" :id="'dropdownInputButton-' + index" data-bs-toggle="dropdown"
          aria-expanded="false">
          <div class="selection-wrapper" :title="filter.selected || $t('message.' + filter.field)">
            {{ filter.selected || $t('message.' + filter.field) }}
          </div>
        </button>
        <a v-if="filter.selected" class="btn text-muted mx-1 clear-button" @click="(event) => {event.stopPropagation(); clearFilter(index); }">
            <i class="bi bi-x text-primary"></i>
          </a>
        <div class="dropdown-menu p-2" :aria-labelledby="'dropdownInputButton-'+index">
          <input v-model="filter.searchTerm" type="text" class="form-control mb-2"
            :placeholder="$t('message.placeholder')" />
          <div class="dropdown-content-scrollable">
            <button v-for="(option, optionIndex) in filteredOptions(filter)" :key="optionIndex"
              class="dropdown-item tuni-dropdown-item" @click="applyFilter(index, option)">
              {{ option }}
            </button>
          </div>

        </div>
      </div>

    </li>
  </ul>
  <button v-if="filters.some(f => f.selected)" type="button" class="btn btn-primary" @click="clearAllFilters">{{$t('message.nollaa_suodattimet')}}</button>
</template>

<style scoped>

.dropdown {
  position: relative;
  width: 100%;
}

.filter-wrapper {
  display: grid;
  gap: 0.5rem;
  box-sizing: border-box;
  flex: 1;
  max-width: 900px;
  min-width: fit-content;
  grid-template-columns: repeat(4, 160px);
}

@media screen and (max-width: 768px){
  .filter-wrapper {
    grid-template-columns: calc(50% - .5rem) calc(50% - .5rem);
  }
}


.filter-wrapper .d-toggle {
  height: 40px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--bs-light-bg-subtle);
  width: 100%;
}


.filter-wrapper .filter-slot {
  position: relative;
  max-width: 100%;
}

.selection-wrapper {
  font-weight: inherit;
  max-width: 70%;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.clear-button {
  padding: 0;
  pointer-events: auto;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  right: 1.5rem;
}
.clear-button:hover {
  background-color: var(--bs-tertiary-bg);
}

.btn-primary {
  margin-left: 0.5rem;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

</style>
