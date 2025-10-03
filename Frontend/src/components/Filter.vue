<script>
import axios from 'axios';

// Define filters
export default {
  name: 'FilterComponent',

  data() {
    return { 
      openDropdown : null,
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
        
        filter.options = res.data.data.map(s => s.trim()).sort((a,b) => a ? b ? a.localeCompare(b) : -1 : 1) || []
      } 
      catch (error) {
        console.error("Error fetching filter option:", error)
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
    }
  },

}
</script>

<template>
  <aside class="w-64 h-screen bg-gray-800 text-black p-2">
    <h2 class="text-lg font-bold mb-4">{{$t('message.suodatin')}}</h2>
    
    <ul class="filter-list">
      <li 
        v-for="(filter, index) in filters" 
        :key="index" 
        class="mb-2"
      >

        <!-- Dropdown Header -->
        <div 
          class="category"
          @click="toggleDropdown(index)"
        >
          <span>{{ filter.selected || $t('message.' + filter.field) }}</span>
          
          <button
            class="reset-button"
            v-if="filter.selected"
            @click.stop="clearFilter(index)"
          >
            x
          </button>
          
          <span class="ml-auto">▼</span>
        </div>

        <!-- Dropdown Options -->
        <ul v-if="openDropdown === index" class="dropdown-content">
          <li class="search-bar">
            <input
              v-model="filter.searchTerm"
              type="text"
              :placeholder="$t('message.placeholder')"
              class="search-input"
            />
          </li>

          <li 
            v-for="(option, optionIndex) in filteredOptions(filter)" 
            :key="optionIndex" 
            class="option"
            @click="applyFilter(index, option)"
          >
            {{ option }}
          </li>
        </ul>
      </li>
    </ul>
  </aside>
</template>

<style scoped>
aside {
  height: 81.7vh;
  background-color: #C3B9D7;
  align-items: top;
  grid-column: 1;
}
ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.category {
  width: 100%; /* Full width */
  padding: 12px;
  border: 1px solid #4b5563; /* Gray border */
  background-color: #ffffff; /* White */
  cursor: pointer;
  display: flex; /* Use flexbox */
  justify-content: space-between; /* Space between the title and the arrow */
  align-items: center; /* Vertically center the text */
  transition: background 0.2s;
}

.category:hover {
  background-color: #e1dde9; /* Lighter gray on hover */
}

.category span:last-child {
  margin-left: auto; /* Push the arrow to the right */
}

.reset-button {
  margin-right: 12px;
  border: none;
  background: none;
  cursor: pointer;
  color: #000000; 
  font-size: 20px;
  font-weight: bold;
}

.reset-button:hover {
  color: #ff0000;
}

/* Option styling */
.option {
  width: 100%; /* Full width */
  padding: 12px;
  border-top: 1px solid #4b5563; /* Border top for separation */
  background-color: #ffffff; /* White */
  cursor: pointer;
  display: flex;
  justify-content: space-between; /* Space between option text and arrow */
  align-items: center; /* Vertically center */
  transition: background 0.2s;
}

.option:hover {
  background-color: #e1dde9; /* Lighter gray on hover */
}

.option span:last-child {
  margin-left: auto; /* Align the arrow to the right */
}

.filter-dropdown {
  width: 200px;
  margin-bottom: 16px;
}

/* Dropdownin sisällön tyylit */
.dropdown-content {
  border: 1px solid #ccc;
  background-color: #fff;
  list-style: none;
  padding: 0;
  margin: 0;
  /* Rajaa korkeus ja lisää scroll */
  max-height: 300px; /* n. 4 itemiä */
  overflow-y: auto;
}

/* Hakukentän rivi */
.search-bar {
  padding: 4px;
  border-bottom: 1px solid #ccc;
  background-color: #f3f3f3;
}

/* Yksittäinen optio */
.option-item {
  padding: 8px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}
.option-item:hover {
  background-color: #e1dde9;
}

.category {
  width: 100%;
  padding: 12px;
  background-color: #ffffff;
  border: 1px solid #ccc;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: background 0.2s;
  justify-content: space-between;
}
.category:hover {
  background-color: #e1dde9;
}
</style>
