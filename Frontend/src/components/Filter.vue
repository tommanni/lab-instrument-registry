<script>
import axios from 'axios';
import { useRouter, useRoute } from 'vue-router'

// Define filters
export default {
  name: 'FilterComponent',

  data() {
    return {
      openDropdown: null,
      filters: []
    }
  },

  emits: ['filter-change', 'all-filters-cleared'],

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

  setup() {
    const router = useRouter()
    const route = useRoute()

    return { router, route }
  },

  mounted() {
    const params = new URLSearchParams(window.location.search);

    this.filters.forEach(filter => {
      const paramValue = params.get(filter.field);
      if (paramValue !== null) {
        filter.selected = paramValue;
      } else {
        filter.selected = null;
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
    filteredOptions(filter) {
      if (!filter.searchTerm) {
        return filter.options
      }

      const lowerTerm = filter.searchTerm.toLowerCase()
      return filter.options.filter(opt =>
        opt.toLowerCase().includes(lowerTerm)
      )
    },

    clearFilter(filterIndex) {
      const filter = this.filters[filterIndex];
      filter.selected = null;
      filter.searchTerm = ''

      this.$emit('filter-change', {
        filterName: filter.field,
        value: null
      })
    },
    
    clearAllFilters() {
      const clearedFilters = {};
      const newQuery = { ...this.route.query }

      this.filters.forEach(filter => {
        filter.selected = null
        filter.searchTerm = ''
        delete newQuery[filter.field]
        clearedFilters[filter.field] = null;
      });

      this.router.replace({ query: newQuery })

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
            :placeholder="$t('message.' + filter.field)" />
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
  <button
    v-if="filters.some(f => f.selected)"
    type="button"
    class="btn btn-primary ms-md-3 clear-filters-button"
    @click="clearAllFilters"
  >
    {{$t('message.nollaa_suodattimet')}}
  </button>
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
  grid-template-columns: repeat(4, 200px);
  padding-bottom: 4px;
}

@media screen and (max-width: 768px){
  .filter-wrapper {
    grid-template-columns: 1fr;
    width: 100%;
    margin-bottom: 0;
  }
  .clear-filters-button {
    width: 100%;
    margin-top: 8px;
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

.clear-filters-button {
  align-self: flex-start;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding-left: 1rem;
  padding-right: 1rem;
  white-space: nowrap;
  flex-shrink: 0;
}


ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

</style>
