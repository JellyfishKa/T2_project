<template>
  <div class="p-6 max-w-6xl mx-auto space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-gray-900">База данных</h1>
      <p class="text-sm text-gray-500 mt-1">Управление данными: загрузка, просмотр, очистка</p>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200">
      <nav class="flex gap-1 -mb-px">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="setActiveTab(tab.id)"
          :class="[
            'px-4 py-2 text-sm font-medium rounded-t border-b-2 transition-colors',
            activeTab === tab.id
              ? 'border-blue-600 text-blue-600 bg-blue-50'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
          ]"
        >
          {{ tab.label }}
        </button>
      </nav>
    </div>

    <!-- Error banner -->
    <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded">
      {{ error }}
    </div>

    <!-- ─── Tab: Локации ─── -->
    <div v-if="activeTab === 'locations'" class="space-y-4">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div class="card p-4 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ locations.length }}</div>
          <div class="text-xs text-gray-500 mt-1">Всего ТТ</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ locCatCount('A') }}</div>
          <div class="text-xs text-gray-500 mt-1">Категория A</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ locCatCount('B') }}</div>
          <div class="text-xs text-gray-500 mt-1">Категория B</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ locCatCount('C') + locCatCount('D') }}</div>
          <div class="text-xs text-gray-500 mt-1">Категории C+D</div>
        </div>
      </div>

      <div class="card p-4 flex flex-wrap gap-3 items-center">
        <label class="btn-secondary cursor-pointer">
          Загрузить XLSX / JSON / CSV
          <input type="file" accept=".xlsx,.json,.csv" class="hidden" @change="handleLocUpload" />
        </label>
        <button class="btn-danger" @click="openClearDialog">Очистить таблицу</button>
        <span v-if="locUploadMsg" class="text-sm" :class="locUploadErr ? 'text-red-600' : 'text-green-700'">
          {{ locUploadMsg }}
        </span>
      </div>

      <div class="card overflow-hidden">
        <div v-if="locLoading" class="p-8 text-center text-gray-500 text-sm">Загрузка…</div>
        <div v-else-if="locations.length === 0" class="p-8 text-center text-gray-500 text-sm">
          Нет локаций — загрузите файл
        </div>
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Название</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Город</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Район</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Кат</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Lat</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Lon</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Действия</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="loc in locPageItems" :key="loc.id" class="hover:bg-gray-50">
              <td class="px-4 py-2 text-gray-900 max-w-xs truncate">{{ loc.name }}</td>
              <td class="px-4 py-2 text-gray-600">{{ loc.city ?? '—' }}</td>
              <td class="px-4 py-2 text-gray-600">{{ loc.district ?? '—' }}</td>
              <td class="px-4 py-2 text-center">
                <span :class="catBadge(loc.category)" class="text-xs px-2 py-0.5 rounded-full font-medium">
                  {{ loc.category ?? '?' }}
                </span>
              </td>
              <td class="px-4 py-2 text-right text-gray-600 font-mono text-xs">{{ loc.lat.toFixed(4) }}</td>
              <td class="px-4 py-2 text-right text-gray-600 font-mono text-xs">{{ loc.lon.toFixed(4) }}</td>
              <td class="px-4 py-2 text-center whitespace-nowrap">
                <button class="text-xs text-blue-600 hover:underline mr-2" @click="openEditLoc(loc)">Изменить</button>
                <button class="btn-danger-sm" @click="doDeleteLoc(loc.id)">Удалить</button>
              </td>
            </tr>
          </tbody>
        </table>
        <!-- Pagination -->
        <div v-if="locPageCount > 1" class="flex items-center justify-between px-4 py-3 border-t border-gray-200">
          <span class="text-sm text-gray-500">
            {{ (locPage - 1) * 50 + 1 }}–{{ Math.min(locPage * 50, locations.length) }} из {{ locations.length }}
          </span>
          <div class="flex items-center gap-1">
            <button
              @click="locPage = 1"
              :disabled="locPage === 1"
              class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >«</button>
            <button
              @click="locPage--"
              :disabled="locPage === 1"
              class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >‹</button>
            <span
              v-for="p in pagesToShow"
              :key="p"
            >
              <button
                v-if="p !== '...'"
                @click="locPage = Number(p)"
                :class="[
                  'px-2.5 py-1 text-xs border rounded',
                  locPage === Number(p)
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'border-gray-300 hover:bg-gray-50'
                ]"
              >{{ p }}</button>
              <span v-else class="px-1 text-xs text-gray-400">…</span>
            </span>
            <button
              @click="locPage++"
              :disabled="locPage === locPageCount"
              class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >›</button>
            <button
              @click="locPage = locPageCount"
              :disabled="locPage === locPageCount"
              class="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >»</button>
          </div>
        </div>
      </div>

      <!-- Clear dialog -->
      <div v-if="showClearDialog" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
          <h3 class="font-semibold text-gray-900 mb-2">Очистить таблицу локаций?</h3>
          <div v-if="clearPreview" class="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-800 mb-4 space-y-1">
            <p>Будет удалено:</p>
            <p>• Локаций (ТТ): <strong>{{ clearPreview.locations }}</strong></p>
            <p>• Записей расписания: <strong>{{ clearPreview.visit_schedule }}</strong></p>
            <p>• Визитов: <strong>{{ clearPreview.visit_log }}</strong></p>
            <p>• Пропущенных (stash): <strong>{{ clearPreview.skipped_visit_stash }}</strong></p>
          </div>
          <p class="text-sm text-gray-600 mb-3">Введите <strong>ОЧИСТИТЬ</strong> для подтверждения:</p>
          <input v-model="clearConfirmText" class="input mb-4" placeholder="ОЧИСТИТЬ" />
          <div class="flex gap-3 justify-end">
            <button class="btn-secondary" @click="showClearDialog = false; clearConfirmText = ''">Отмена</button>
            <button
              class="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm px-4 py-2 rounded"
              :disabled="clearConfirmText !== 'ОЧИСТИТЬ' || clearing"
              @click="executeClear"
            >
              {{ clearing ? 'Удаление…' : 'Удалить всё' }}
            </button>
          </div>
        </div>
      </div>
    <!-- Edit location modal -->
    <div v-if="editingLoc" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 max-w-lg w-full mx-4">
        <h3 class="font-semibold text-gray-900 mb-4">Редактировать точку</h3>
        <div class="grid grid-cols-2 gap-3">
          <div class="col-span-2">
            <label class="label">Название</label>
            <input v-model="editLocForm.name" class="input" />
          </div>
          <div>
            <label class="label">Город</label>
            <input v-model="editLocForm.city" class="input" placeholder="Саранск" />
          </div>
          <div>
            <label class="label">Район</label>
            <input v-model="editLocForm.district" class="input" />
          </div>
          <div>
            <label class="label">Категория</label>
            <select v-model="editLocForm.category" class="input">
              <option value="">—</option>
              <option value="A">A</option>
              <option value="B">B</option>
              <option value="C">C</option>
              <option value="D">D</option>
            </select>
          </div>
          <div>
            <label class="label">Адрес</label>
            <input v-model="editLocForm.address" class="input" />
          </div>
          <div>
            <label class="label">Широта (lat)</label>
            <input v-model.number="editLocForm.lat" type="number" step="0.0001" class="input" />
          </div>
          <div>
            <label class="label">Долгота (lon)</label>
            <input v-model.number="editLocForm.lon" type="number" step="0.0001" class="input" />
          </div>
        </div>
        <div class="flex gap-3 justify-end mt-5">
          <button class="btn-secondary" @click="editingLoc = null">Отмена</button>
          <button class="btn-primary" :disabled="savingLoc" @click="saveEditLoc">
            {{ savingLoc ? 'Сохранение…' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Force-delete location dialog -->
    <div v-if="forceDeleteLocId" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <h3 class="font-semibold text-gray-900 mb-2">Точка связана с расписанием</h3>
        <p class="text-sm text-gray-600 mb-5">
          Удаление точки удалит все связанные записи расписания и визитов.
          После удаления рекомендуется пересобрать месячный план.
        </p>
        <div class="flex gap-3 justify-end">
          <button class="btn-secondary" @click="forceDeleteLocId = null">Отмена</button>
          <button class="bg-red-600 hover:bg-red-700 text-white text-sm px-4 py-2 rounded font-medium" @click="forceDeleteLoc">
            Удалить принудительно
          </button>
        </div>
      </div>
    </div>

    </div>

    <!-- ─── Tab: Автомобили ─── -->
    <div v-if="activeTab === 'vehicles'" class="space-y-4">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div class="card p-4 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ vehicles.length }}</div>
          <div class="text-xs text-gray-500 mt-1">Автомобилей</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-lg font-bold text-gray-900">{{ avgCityConsumption }}</div>
          <div class="text-xs text-gray-500 mt-1">Ср. расход (город)</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-lg font-bold text-gray-900">{{ avgHighwayConsumption }}</div>
          <div class="text-xs text-gray-500 mt-1">Ср. расход (трасса)</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-lg font-bold text-gray-900">{{ avgFuelPrice }}</div>
          <div class="text-xs text-gray-500 mt-1">Ср. цена топлива</div>
        </div>
      </div>

      <div class="card p-5">
        <h2 class="font-semibold text-gray-800 mb-4">Добавить автомобиль</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label class="label">Название</label>
            <input v-model="vForm.name" class="input" placeholder="Lada Granta" />
          </div>
          <div>
            <label class="label">Цена топлива (₽/л)</label>
            <input v-model.number="vForm.fuel_price_rub" type="number" min="0" step="0.5" class="input" placeholder="63" />
          </div>
          <div>
            <label class="label">Расход город (л/100км)</label>
            <input v-model.number="vForm.consumption_city_l_100km" type="number" min="0" step="0.1" class="input" placeholder="9.0" />
          </div>
          <div>
            <label class="label">Расход трасса (л/100км)</label>
            <input v-model.number="vForm.consumption_highway_l_100km" type="number" min="0" step="0.1" class="input" placeholder="6.5" />
          </div>
        </div>
        <div class="flex gap-2 mt-4">
          <button class="btn-primary" :disabled="!isVFormValid || vSaving" @click="addVehicle">
            {{ vSaving ? 'Сохранение…' : 'Добавить' }}
          </button>
          <label class="btn-secondary cursor-pointer">
            Загрузить JSON
            <input type="file" accept=".json" class="hidden" @change="handleVehicleUpload" />
          </label>
        </div>
      </div>

      <div class="card overflow-hidden">
        <div v-if="vLoading" class="p-8 text-center text-gray-500 text-sm">Загрузка…</div>
        <div v-else-if="vehicles.length === 0" class="p-8 text-center text-gray-500 text-sm">
          Нет автомобилей — добавьте вручную или загрузите JSON
        </div>
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Название</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">₽/л</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">л/100км город</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">л/100км трасса</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">₽/100км город</th>
              <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Действия</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="v in vehicles" :key="v.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 font-medium text-gray-900">{{ v.name }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ v.fuel_price_rub.toFixed(1) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ v.consumption_city_l_100km.toFixed(1) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ v.consumption_highway_l_100km.toFixed(1) }}</td>
              <td class="px-4 py-3 text-right text-gray-700">
                {{ ((v.consumption_city_l_100km / 100) * v.fuel_price_rub * 100).toFixed(0) }}
              </td>
              <td class="px-4 py-3 text-center whitespace-nowrap">
                <button class="text-xs text-blue-600 hover:underline mr-2" @click="openEditVehicle(v)">Изменить</button>
                <button class="btn-danger-sm" @click="removeVehicle(v.id)">Удалить</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Edit vehicle modal -->
    <div v-if="editingVehicle" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <h3 class="font-semibold text-gray-900 mb-4">Редактировать автомобиль</h3>
        <div class="grid grid-cols-2 gap-3">
          <div class="col-span-2">
            <label class="label">Название</label>
            <input v-model="vEditForm.name" class="input" />
          </div>
          <div>
            <label class="label">Цена топлива (₽/л)</label>
            <input v-model.number="vEditForm.fuel_price_rub" type="number" min="0" step="0.5" class="input" />
          </div>
          <div>
            <label class="label">Расход город (л/100км)</label>
            <input v-model.number="vEditForm.consumption_city_l_100km" type="number" min="0" step="0.1" class="input" />
          </div>
          <div class="col-span-2">
            <label class="label">Расход трасса (л/100км)</label>
            <input v-model.number="vEditForm.consumption_highway_l_100km" type="number" min="0" step="0.1" class="input" />
          </div>
        </div>
        <div class="flex gap-3 justify-end mt-5">
          <button class="btn-secondary" @click="editingVehicle = null">Отмена</button>
          <button class="btn-primary" :disabled="savingVehicle" @click="saveEditVehicle">
            {{ savingVehicle ? 'Сохранение…' : 'Сохранить' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ─── Tab: Сотрудники ─── -->
    <div v-if="activeTab === 'employees'" class="space-y-4">
      <div class="grid grid-cols-3 gap-4">
        <div class="card p-4 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ reps.length }}</div>
          <div class="text-xs text-gray-500 mt-1">Всего</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-2xl font-bold text-green-700">{{ reps.filter(r => r.status === 'active').length }}</div>
          <div class="text-xs text-gray-500 mt-1">Активных</div>
        </div>
        <div class="card p-4 text-center">
          <div class="text-2xl font-bold text-amber-600">{{ reps.filter(r => r.status !== 'active').length }}</div>
          <div class="text-xs text-gray-500 mt-1">Нуждаются внимания</div>
        </div>
      </div>

      <div v-if="repDeleteWarning" class="bg-amber-50 border border-amber-300 text-amber-800 text-sm px-4 py-3 rounded flex items-center justify-between">
        <span>⚠ {{ repDeleteWarning }}</span>
        <button class="ml-4 text-amber-600 hover:text-amber-800 font-medium text-xs" @click="repDeleteWarning = null">✕</button>
      </div>

      <div class="card p-4 flex justify-end">
        <button class="btn-primary" @click="showRepForm = !showRepForm">
          {{ showRepForm ? 'Свернуть' : '+ Добавить сотрудника' }}
        </button>
      </div>

      <div v-if="showRepForm" class="card p-5">
        <div class="grid gap-3 md:grid-cols-[1fr_200px_220px_auto_auto] md:items-end">
          <div>
            <label class="label">ФИО</label>
            <input v-model="newRepName" class="input" placeholder="Иванов Иван Иванович" />
          </div>
          <div>
            <label class="label">Автомобиль</label>
            <select v-model="newRepVehicleId" class="input" data-testid="new-rep-vehicle-select-db">
              <option :value="null">Такси / Автобус</option>
              <option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.name }}</option>
            </select>
          </div>
          <div>
            <label class="label">Статус</label>
            <select v-model="newRepStatus" class="input">
              <option value="active">Активен</option>
              <option value="sick">На больничном</option>
              <option value="vacation">В отпуске</option>
              <option value="unavailable">Недоступен</option>
            </select>
          </div>
          <button class="btn-primary" :disabled="repSaving" @click="doCreateRep">
            {{ repSaving ? 'Сохранение…' : 'Сохранить' }}
          </button>
          <button class="btn-secondary" @click="showRepForm = false">Отмена</button>
        </div>
      </div>

      <div v-if="rLoading" class="card p-8 text-center text-gray-500 text-sm">Загрузка…</div>
      <div v-else class="grid gap-3">
        <div
          v-for="rep in reps"
          :key="rep.id"
          class="card p-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between"
        >
          <div>
            <div v-if="editingRepId === rep.id" class="flex items-center gap-2">
              <input v-model="editRepName" class="input-sm w-48" @keyup.enter="saveRepName" @keyup.escape="editingRepId = null" />
              <button class="btn-primary text-xs px-2 py-1" @click="saveRepName">OK</button>
              <button class="btn-secondary text-xs px-2 py-1" @click="editingRepId = null">✕</button>
            </div>
            <div v-else class="flex items-center gap-2">
              <span class="font-medium text-gray-900">{{ rep.name }}</span>
              <button class="text-xs text-blue-600 hover:underline" @click="startEditRepName(rep)">Изменить</button>
            </div>
            <div class="text-xs text-gray-400 mt-0.5">{{ rep.id.slice(0, 8) }}…</div>
            <span v-if="rep.vehicle_name" class="text-xs text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full mt-1 inline-block">
              🚗 {{ rep.vehicle_name }}
            </span>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <select
              :value="rep.status"
              class="input-sm"
              @change="doUpdateStatus(rep.id, ($event.target as HTMLSelectElement).value)"
            >
              <option value="active">Активен</option>
              <option value="sick">На больничном</option>
              <option value="vacation">В отпуске</option>
              <option value="unavailable">Недоступен</option>
            </select>
            <select
              :value="rep.vehicle_id ?? ''"
              class="input-sm"
              @change="doAssignVehicle(rep.id, ($event.target as HTMLSelectElement).value || null)"
            >
              <option value="">Такси / Автобус</option>
              <option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.name }}</option>
            </select>
            <button class="btn-danger-sm" @click="doDeleteRep(rep.id)">Удалить</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ─── Tab: Аудит ─── -->
    <div v-if="activeTab === 'audit'" class="space-y-4">
      <div class="flex gap-3 items-center">
        <label class="text-sm text-gray-700 font-medium">Месяц:</label>
        <input v-model="auditMonth" type="month" class="input w-40" @change="loadAudit(true)" />
        <span class="text-sm text-gray-500">Всего: {{ auditTotal }}</span>
      </div>

      <div class="card overflow-hidden">
        <div v-if="auditLoading" class="p-8 text-center text-gray-500 text-sm">Загрузка…</div>
        <div v-else-if="auditItems.length === 0" class="p-8 text-center text-gray-500 text-sm">
          Нет записей за этот месяц
        </div>
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Дата/время</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Действие</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Объект</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Было → Стало</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="item in auditItems" :key="item.id" class="hover:bg-gray-50">
              <td class="px-4 py-2 text-gray-500 whitespace-nowrap text-xs font-mono">
                {{ item.created_at ? item.created_at.replace('T', ' ').slice(0, 19) : '—' }}
              </td>
              <td class="px-4 py-2 text-gray-900">{{ item.action_label }}</td>
              <td class="px-4 py-2 text-gray-600 text-xs">
                {{ item.table_name }}<br />
                <span class="text-gray-400">{{ item.record_id?.slice(0, 8) }}…</span>
              </td>
              <td class="px-4 py-2 text-xs text-gray-600 max-w-sm truncate">
                <span v-if="item.old_value" class="text-red-600">{{ truncate(item.old_value) }}</span>
                <span v-if="item.old_value && item.new_value"> → </span>
                <span v-if="item.new_value" class="text-green-700">{{ truncate(item.new_value) }}</span>
                <span v-if="!item.old_value && !item.new_value" class="text-gray-400">{{ truncate(item.details) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="auditItems.length < auditTotal" class="p-3 border-t flex justify-center">
          <button class="btn-secondary text-sm" :disabled="auditLoading" @click="loadAudit(false)">
            Загрузить ещё
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Location, Vehicle, SalesRep, AuditLogItem } from '@/services/types'
import {
  fetchAllLocations, updateLocation, deleteLocation,
  fetchVehicles, createVehicle, updateVehicle, deleteVehicle, uploadVehiclesJson,
  fetchReps, createRep, updateRep, deleteRep as apiDeleteRep,
  uploadLocations, previewClearLocations, clearAllLocations,
  fetchAuditLog,
  getApiErrorMessage,
} from '@/services/api'

// ─── Tabs ─────────────────────────────────────────────────────────────────────
const route = useRoute()
const router = useRouter()

const tabIds = ['locations', 'vehicles', 'employees', 'audit'] as const
type DatabaseTabId = typeof tabIds[number]

const tabs: Array<{ id: DatabaseTabId; label: string }> = [
  { id: 'locations' as const, label: 'Локации (ТТ)' },
  { id: 'vehicles'  as const, label: 'Автомобили' },
  { id: 'employees' as const, label: 'Сотрудники' },
  { id: 'audit'     as const, label: 'Аудит-лог' },
]

function normalizeTab(value: unknown): DatabaseTabId {
  const candidate = Array.isArray(value) ? value[0] : value
  return tabIds.includes(candidate as DatabaseTabId)
    ? (candidate as DatabaseTabId)
    : 'locations'
}

const activeTab = ref<DatabaseTabId>(normalizeTab(route.query.tab))
const error = ref<string | null>(null)

function setActiveTab(tab: DatabaseTabId) {
  activeTab.value = tab
}

watch(
  () => route.query.tab,
  (nextQueryTab) => {
    const nextTab = normalizeTab(nextQueryTab)
    if (nextTab !== activeTab.value) {
      activeTab.value = nextTab
    }
  }
)

watch(activeTab, (nextTab) => {
  const currentTab = normalizeTab(route.query.tab)
  const hasExplicitTab = typeof route.query.tab === 'string'

  if (nextTab === currentTab && (hasExplicitTab || nextTab === 'locations')) {
    return
  }

  const nextQuery = { ...route.query }
  if (nextTab === 'locations') {
    delete nextQuery.tab
  } else {
    nextQuery.tab = nextTab
  }

  void router.replace({ query: nextQuery })
})

// ─── Locations ────────────────────────────────────────────────────────────────
const locations = ref<Location[]>([])
const locLoading = ref(false)
const locUploadMsg = ref<string | null>(null)
const locUploadErr = ref(false)
const showClearDialog = ref(false)
const clearPreview = ref<{ locations: number; visit_schedule: number; visit_log: number; skipped_visit_stash: number } | null>(null)
const clearConfirmText = ref('')
const clearing = ref(false)

// Pagination for locations
const locPage = ref(1)
const locPageSize = 50

const locPageCount = computed(() => Math.max(1, Math.ceil(locations.value.length / locPageSize)))
const locPageItems = computed(() => {
  const start = (locPage.value - 1) * locPageSize
  return locations.value.slice(start, start + locPageSize)
})

const pagesToShow = computed(() => {
  const total = locPageCount.value
  const current = locPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages: (number | '...')[] = [1]
  if (current > 3) pages.push('...')
  for (let p = Math.max(2, current - 1); p <= Math.min(total - 1, current + 1); p++) pages.push(p)
  if (current < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

// Reset page when locations reload
watch(locations, () => { locPage.value = 1 })

function locCatCount(cat: string) {
  return locations.value.filter(l => l.category === cat).length
}

function catBadge(cat: string | null | undefined) {
  return {
    A: 'bg-red-100 text-red-800',
    B: 'bg-orange-100 text-orange-800',
    C: 'bg-blue-100 text-blue-800',
    D: 'bg-gray-100 text-gray-700',
  }[cat ?? ''] ?? 'bg-gray-100 text-gray-600'
}

function getUploadedLocations(result: Awaited<ReturnType<typeof uploadLocations>>): Location[] {
  if (Array.isArray(result.created)) return result.created
  if (Array.isArray(result.locations)) return result.locations
  return []
}

async function loadLocations() {
  locLoading.value = true
  try {
    const data = await fetchAllLocations()
    locations.value = Array.isArray(data) ? data : []
  } catch (e) {
    error.value = getApiErrorMessage(e, 'Ошибка загрузки локаций')
  } finally {
    locLoading.value = false
  }
}

async function handleLocUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  locUploadMsg.value = null
  locUploadErr.value = false
  try {
    const result = await uploadLocations(file)
    const created = getUploadedLocations(result)
    const errCount = Array.isArray(result.errors) ? result.errors.length : 0
    if (created.length) {
      // Показываем свежезагруженные точки сразу, даже если follow-up GET вернул пусто.
      locations.value = created
    }
    await loadLocations()
    if (!locations.value.length && created.length) {
      locations.value = created
    }
    locUploadMsg.value = `Загружено: ${created.length || result.total_processed || '?'}${errCount ? `, ошибок: ${errCount}` : ''}`
  } catch (e: any) {
    locUploadErr.value = true
    locUploadMsg.value = `Ошибка: ${getApiErrorMessage(e, 'не удалось загрузить файл')}`
  } finally {
    target.value = ''
  }
}

async function openClearDialog() {
  clearPreview.value = null
  clearConfirmText.value = ''
  showClearDialog.value = true
  try {
    clearPreview.value = await previewClearLocations()
  } catch {
    // preview optional
  }
}

async function executeClear() {
  if (clearConfirmText.value !== 'ОЧИСТИТЬ') return
  clearing.value = true
  try {
    await clearAllLocations()
    showClearDialog.value = false
    clearConfirmText.value = ''
    await loadLocations()
    locUploadMsg.value = 'Таблица очищена'
  } catch (e: any) {
    error.value = `Ошибка очистки: ${getApiErrorMessage(e, 'не удалось очистить данные')}`
  } finally {
    clearing.value = false
  }
}

// ─── Location edit / single delete ────────────────────────────────────────────
const editingLoc = ref<Location | null>(null)
const editLocForm = ref({ name: '', city: '', district: '', address: '', category: '' as '' | 'A' | 'B' | 'C' | 'D', lat: 0, lon: 0 })
const savingLoc = ref(false)
const forceDeleteLocId = ref<string | null>(null)

function openEditLoc(loc: Location) {
  editingLoc.value = loc
  editLocForm.value = {
    name: loc.name,
    city: loc.city ?? '',
    district: loc.district ?? '',
    address: (loc as any).address ?? '',
    category: (loc.category ?? '') as '' | 'A' | 'B' | 'C' | 'D',
    lat: loc.lat,
    lon: loc.lon,
  }
}

async function saveEditLoc() {
  if (!editingLoc.value || savingLoc.value) return
  savingLoc.value = true
  try {
    const updated = await updateLocation(editingLoc.value.id, {
      name: editLocForm.value.name || undefined,
      city: editLocForm.value.city || undefined,
      district: editLocForm.value.district || undefined,
      address: editLocForm.value.address || undefined,
      category: (editLocForm.value.category as 'A' | 'B' | 'C' | 'D') || undefined,
      lat: editLocForm.value.lat,
      lon: editLocForm.value.lon,
    })
    const idx = locations.value.findIndex(l => l.id === updated.id)
    if (idx !== -1) locations.value[idx] = updated
    editingLoc.value = null
  } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка сохранения') }
  finally { savingLoc.value = false }
}

async function doDeleteLoc(id: string) {
  try {
    await deleteLocation(id)
    locations.value = locations.value.filter(l => l.id !== id)
  } catch (e: any) {
    if (e?.response?.status === 409) {
      forceDeleteLocId.value = id
    } else {
      error.value = getApiErrorMessage(e, 'Ошибка удаления точки')
    }
  }
}

async function forceDeleteLoc() {
  if (!forceDeleteLocId.value) return
  try {
    await deleteLocation(forceDeleteLocId.value, true)
    locations.value = locations.value.filter(l => l.id !== forceDeleteLocId.value)
    locUploadMsg.value = 'Точка удалена. Рекомендуется пересобрать месячный план.'
    locUploadErr.value = false
  } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка принудительного удаления') }
  finally { forceDeleteLocId.value = null }
}

// ─── Vehicles ─────────────────────────────────────────────────────────────────
const vehicles = ref<Vehicle[]>([])
const vLoading = ref(false)
const vSaving = ref(false)
const vForm = ref({ name: '', fuel_price_rub: null as number | null, consumption_city_l_100km: null as number | null, consumption_highway_l_100km: null as number | null })

const isVFormValid = computed(() =>
  vForm.value.name.trim() &&
  (vForm.value.fuel_price_rub ?? 0) > 0 &&
  (vForm.value.consumption_city_l_100km ?? 0) > 0 &&
  (vForm.value.consumption_highway_l_100km ?? 0) > 0
)

const avgCityConsumption = computed(() => {
  if (!vehicles.value.length) return '—'
  const avg = vehicles.value.reduce((s, v) => s + v.consumption_city_l_100km, 0) / vehicles.value.length
  return `${avg.toFixed(1)} л/100км`
})
const avgHighwayConsumption = computed(() => {
  if (!vehicles.value.length) return '—'
  const avg = vehicles.value.reduce((s, v) => s + v.consumption_highway_l_100km, 0) / vehicles.value.length
  return `${avg.toFixed(1)} л/100км`
})
const avgFuelPrice = computed(() => {
  if (!vehicles.value.length) return '—'
  const avg = vehicles.value.reduce((s, v) => s + v.fuel_price_rub, 0) / vehicles.value.length
  return `${avg.toFixed(1)} ₽/л`
})

async function loadVehicles() {
  vLoading.value = true
  try { vehicles.value = await fetchVehicles() } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка загрузки автомобилей') } finally { vLoading.value = false }
}

async function addVehicle() {
  if (!isVFormValid.value || vSaving.value) return
  vSaving.value = true
  try {
    const v = await createVehicle({
      name: vForm.value.name.trim(),
      fuel_price_rub: vForm.value.fuel_price_rub!,
      consumption_city_l_100km: vForm.value.consumption_city_l_100km!,
      consumption_highway_l_100km: vForm.value.consumption_highway_l_100km!,
    })
    vehicles.value.push(v)
    vForm.value = { name: '', fuel_price_rub: null, consumption_city_l_100km: null, consumption_highway_l_100km: null }
  } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка добавления автомобиля') } finally { vSaving.value = false }
}

async function removeVehicle(id: string) {
  if (!confirm('Удалить автомобиль? Сотрудники потеряют привязку.')) return
  try {
    await deleteVehicle(id)
    vehicles.value = vehicles.value.filter(v => v.id !== id)
  } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка удаления автомобиля') }
}

const editingVehicle = ref<Vehicle | null>(null)
const vEditForm = ref({ name: '', fuel_price_rub: 0, consumption_city_l_100km: 0, consumption_highway_l_100km: 0 })
const savingVehicle = ref(false)

function openEditVehicle(v: Vehicle) {
  editingVehicle.value = v
  vEditForm.value = { name: v.name, fuel_price_rub: v.fuel_price_rub, consumption_city_l_100km: v.consumption_city_l_100km, consumption_highway_l_100km: v.consumption_highway_l_100km }
}

async function saveEditVehicle() {
  if (!editingVehicle.value || savingVehicle.value) return
  savingVehicle.value = true
  try {
    const updated = await updateVehicle(editingVehicle.value.id, vEditForm.value)
    const idx = vehicles.value.findIndex(v => v.id === updated.id)
    if (idx !== -1) vehicles.value[idx] = updated
    editingVehicle.value = null
  } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка сохранения автомобиля') }
  finally { savingVehicle.value = false }
}

async function handleVehicleUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  try {
    const result = await uploadVehiclesJson(file)
    vehicles.value.push(...result.created)
    if (result.errors.length) error.value = `Загружено: ${result.created.length}, ошибок: ${result.errors.length}`
  } catch (e: any) {
    error.value = `Ошибка загрузки: ${getApiErrorMessage(e, 'не удалось загрузить JSON')}`
  } finally { target.value = '' }
}

// ─── Employees ────────────────────────────────────────────────────────────────
const reps = ref<SalesRep[]>([])
const rLoading = ref(false)
const repSaving = ref(false)
const showRepForm = ref(false)
const newRepName = ref('')
const newRepStatus = ref<SalesRep['status']>('active')
const newRepVehicleId = ref<string | null>(null)
const repDeleteWarning = ref<string | null>(null)
const editingRepId = ref<string | null>(null)
const editRepName = ref('')

async function loadReps() {
  rLoading.value = true
  try { reps.value = await fetchReps() } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка загрузки сотрудников') } finally { rLoading.value = false }
}

async function doCreateRep() {
  if (!newRepName.value.trim() || repSaving.value) return
  repSaving.value = true
  try {
    await createRep(newRepName.value.trim(), newRepStatus.value, newRepVehicleId.value)
    newRepName.value = ''
    newRepVehicleId.value = null
    showRepForm.value = false
    await loadReps()
  } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка создания сотрудника') } finally { repSaving.value = false }
}

async function doUpdateStatus(id: string, status: string) {
  try {
    await updateRep(id, { status: status as SalesRep['status'] })
    await loadReps()
  } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка обновления статуса') }
}

async function doAssignVehicle(id: string, vehicleId: string | null) {
  try {
    const updated = await updateRep(id, { vehicle_id: vehicleId })
    const idx = reps.value.findIndex(r => r.id === id)
    if (idx !== -1) reps.value[idx] = updated
  } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка привязки автомобиля') }
}

async function startEditRepName(rep: SalesRep) {
  editingRepId.value = rep.id
  editRepName.value = rep.name
}

async function saveRepName() {
  if (!editingRepId.value) return
  try {
    const updated = await updateRep(editingRepId.value, { name: editRepName.value.trim() })
    const idx = reps.value.findIndex(r => r.id === editingRepId.value)
    if (idx !== -1) reps.value[idx] = updated
    editingRepId.value = null
  } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка сохранения имени') }
}

async function doDeleteRep(id: string) {
  const rep = reps.value.find(r => r.id === id)
  if (!rep || !confirm(`Удалить сотрудника ${rep.name}?`)) return
  repDeleteWarning.value = null
  try {
    await apiDeleteRep(id)
    reps.value = reps.value.filter(r => r.id !== id)
  } catch (e: any) {
    if (e?.response?.status === 409) {
      if (!confirm(`У ${rep.name} есть данные в расписании.\nСотрудник будет переведён в "Недоступен" и удалён принудительно.\nПосле этого рекомендуется пересобрать план.`)) return
      try {
        await updateRep(id, { status: 'unavailable' })
        await apiDeleteRep(id, true)
        reps.value = reps.value.filter(r => r.id !== id)
        repDeleteWarning.value = `Сотрудник ${rep.name} удалён. Рекомендуется пересобрать месячный план.`
      } catch (e2) { error.value = getApiErrorMessage(e2, 'Ошибка принудительного удаления') }
    } else {
      error.value = getApiErrorMessage(e, 'Ошибка удаления сотрудника')
    }
  }
}

// ─── Audit ────────────────────────────────────────────────────────────────────
const auditItems = ref<AuditLogItem[]>([])
const auditTotal = ref(0)
const auditLoading = ref(false)
const auditMonth = ref(new Date().toISOString().slice(0, 7))

async function loadAudit(reset: boolean) {
  auditLoading.value = true
  if (reset) auditItems.value = []
  try {
    const result = await fetchAuditLog(auditMonth.value, 50, auditItems.value.length)
    auditTotal.value = result.total
    auditItems.value.push(...result.items)
  } catch (e) { error.value = getApiErrorMessage(e, 'Ошибка загрузки аудит-лога') } finally { auditLoading.value = false }
}

function truncate(val: string | null | undefined, max = 80): string {
  if (!val) return ''
  return val.length > max ? val.slice(0, max) + '…' : val
}

// ─── Init ─────────────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.allSettled([loadLocations(), loadVehicles(), loadReps()])
  await loadAudit(true)
})
</script>

<style scoped>
.card { @apply bg-white rounded-lg border border-gray-200 shadow-sm; }
.input { @apply bg-white border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500; }
.input-sm { @apply bg-white border border-gray-300 rounded px-2 py-1 text-sm text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-500; }
.label { @apply block text-sm text-gray-600 mb-1; }
.btn-primary { @apply bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-2 rounded; }
.btn-secondary { @apply bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 text-sm px-4 py-2 rounded; }
.btn-danger { @apply bg-red-600 hover:bg-red-700 text-white text-sm px-4 py-2 rounded; }
.btn-danger-sm { @apply bg-red-600 hover:bg-red-700 text-white text-xs px-3 py-1 rounded; }
</style>
