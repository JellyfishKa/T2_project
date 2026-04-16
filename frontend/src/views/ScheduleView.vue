<template>
  <div class="schedule-view space-y-6 py-6">
    <PageHero
      eyebrow="Операционный план"
      title="Расписание маршрутов"
      description="Планируйте дни торговых представителей, применяйте маршруты ИИ и вручную доводите порядок точек без перегрузки таблицами."
    >
      <template #meta>
        <div class="flex flex-wrap items-center gap-2">
          <button class="btn-icon" @click="shiftMonth(-1)">◀</button>
          <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-sm font-medium text-slate-700 min-w-[8rem] text-center">{{ monthLabel }}</span>
          <button class="btn-icon" @click="shiftMonth(1)">▶</button>
        </div>
      </template>
      <template #actions>
        <button class="btn-primary" @click="openGenerateModal">Сгенерировать план</button>
        <button class="btn-secondary" @click="showHolidays = true">Праздники</button>
        <button class="btn-secondary" @click="showFM = true">Форс-мажор</button>
        <button
          class="btn-secondary flex items-center gap-1.5"
          :disabled="exportLoading"
          @click="handleExport"
          title="Скачать Excel с расписанием и аналитикой"
        >
          <svg v-if="exportLoading" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
          </svg>
          <svg v-else class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
          </svg>
          <span>{{ exportLoading ? 'Экспорт…' : 'Excel' }}</span>
        </button>
      </template>
    </PageHero>

    <!-- Легенда категорий -->
    <div class="flex gap-3 mb-4 text-sm">
      <span v-for="cat in ['A','B','C','D']" :key="cat" class="flex items-center gap-1">
        <span :class="catDot(cat)"></span>{{ cat }}
      </span>
      <span class="flex items-center gap-2 ml-4">
        <span class="w-3 h-3 rounded-full bg-green-600"></span><span class="text-green-700">выполнен</span>
        <span class="w-3 h-3 rounded-full bg-red-700 ml-2"></span><span class="text-red-700">пропущен</span>
      </span>
    </div>

    <!-- Стеш: пропущенные визиты, ожидающие перераспределения -->
    <div v-if="skippedStash.length" class="card p-4 border border-amber-200 bg-amber-50">
      <div class="flex items-center justify-between mb-3">
        <h3 class="font-semibold text-sm text-amber-800">
          Пропущенные точки ({{ skippedStash.length }}) — ожидают переноса
        </h3>
        <button
          v-if="skippedStash.length > 1"
          class="btn-secondary text-xs"
          :disabled="stashLoading"
          @click="resolveAllAI"
        >
          Перераспределить все через ИИ
        </button>
      </div>
      <div
        v-for="entry in skippedStash"
        :key="entry.id"
        class="flex items-center gap-3 py-2 border-b border-amber-100 last:border-0 flex-wrap"
      >
        <span class="text-xs text-gray-500 w-24 shrink-0">{{ entry.original_date }}</span>
        <span class="text-xs font-medium text-gray-800 flex-1 min-w-0 truncate">{{ entry.location_name }}</span>
        <span class="text-xs text-gray-500 shrink-0">{{ entry.rep_name }}</span>
        <div class="flex gap-2 ml-auto shrink-0">
          <button class="btn-secondary text-xs" :disabled="stashLoading" @click="openStashModal(entry)">Назначить</button>
          <button class="btn-secondary text-xs" :disabled="stashLoading" @click="resolveCarryOver(entry.id)">Авто</button>
          <button class="text-xs text-red-500 hover:text-red-700 px-1" :disabled="stashLoading" @click="discardStash(entry.id)" title="Отменить">✕</button>
        </div>
      </div>
    </div>

    <!-- Модал: ручное назначение из стеша -->
    <div v-if="stashModalEntry" class="modal-overlay" @click.self="stashModalEntry = null">
      <div class="modal">
        <h2 class="font-semibold text-lg mb-3">Назначить вручную</h2>
        <p class="text-sm text-gray-700 mb-4">
          <strong>{{ stashModalEntry.location_name }}</strong>
          <span class="text-gray-500 ml-2">{{ stashModalEntry.original_date }}</span>
        </p>
        <div class="space-y-3">
          <div>
            <label class="label">Сотрудник</label>
            <select v-model="stashManualRepId" class="input">
              <option v-for="rep in reps" :key="rep.id" :value="rep.id">{{ rep.name }}</option>
            </select>
          </div>
          <div>
            <label class="label">Дата</label>
            <input v-model="stashManualDate" type="date" class="input" />
          </div>
        </div>
        <div class="flex gap-3 justify-end mt-4">
          <button class="btn-secondary" @click="stashModalEntry = null">Отмена</button>
          <button
            class="btn-primary"
            :disabled="stashLoading || !stashManualRepId || !stashManualDate"
            @click="submitStashManual"
          >
            {{ stashLoading ? 'Сохранение…' : 'Назначить' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Загрузка / ошибка -->
    <div v-if="loading" class="text-gray-500">Загрузка расписания…</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>

    <!-- Таблица по дням -->
    <div v-else class="space-y-2">
      <div
        v-for="route in sortedRoutes"
        :key="route.rep_id + route.date"
        class="card p-3"
      >
        <div
          class="flex items-center gap-3 mb-2 cursor-pointer hover:text-blue-700 transition-colors"
          @click="openDayModal(route)"
        >
          <span class="font-medium text-sm text-gray-900">{{ route.date }}</span>
          <span class="text-blue-600 font-medium">{{ route.rep_name }}</span>
          <span
            class="text-[11px] px-2 py-0.5 rounded-full"
            :class="routeSourceBadgeClass(route.route_source)"
          >
            {{ routeSourceLabel(route.route_source) }}
          </span>
          <span v-if="route.route_label" class="text-xs text-gray-500 truncate max-w-[12rem]">
            {{ route.route_label }}
          </span>
          <span class="text-gray-500 text-xs">
            {{ route.total_tt }} ТТ · ~{{ route.estimated_duration_hours }}ч
          </span>
          <span class="text-gray-400 text-xs ml-auto">↗ детали</span>
        </div>
        <div class="flex flex-wrap gap-1 items-center">
          <template v-for="(visit, idx) in route.visits" :key="visit.id">
            <!-- Разделитель обеда после 7-го визита -->
            <div
              v-if="route.lunch_break_at && idx === 7"
              class="w-full flex items-center gap-2 my-1 text-xs text-yellow-700"
            >
              <span>🍽</span>
              <span>Обед {{ route.lunch_break_at }}</span>
              <div class="flex-1 border-t border-yellow-300"></div>
            </div>
            <span
              :class="visitChipClass(visit)"
              :title="`${visit.location_name} [${visit.location_category ?? '?'}] — ${visit.status}${visit.time_in ? ' · вход ' + visit.time_in : ''}${visit.time_out ? ' · выход ' + visit.time_out : ''}`"
              class="visit-chip cursor-pointer hover:opacity-80"
              @click="openVisitModal(visit)"
            >
              {{ visit.location_category ?? '?' }} · {{ visit.location_name.slice(0, 18) }}
              <span v-if="visit.status === 'completed'">
                <span class="ml-0.5">✓</span>
                <span v-if="visitDuration(visit)" class="ml-0.5 opacity-75">{{ visitDuration(visit) }}м</span>
              </span>
              <span v-else-if="visit.status === 'skipped'" class="ml-0.5">✗</span>
            </span>
          </template>
        </div>
      </div>
      <div v-if="!sortedRoutes.length" class="text-gray-500 text-sm">
        Нет маршрутов за {{ monthLabel }}. Нажмите «Сгенерировать план».
      </div>
    </div>

    <!-- Модал: генерация плана -->
    <div v-if="showGenerate" class="modal-overlay" @click.self="showGenerate = false">
      <div class="modal">
        <h2 class="font-semibold text-lg mb-4 text-gray-900">Сгенерировать план</h2>
        <p class="text-sm text-gray-600 mb-2">
          Месяц: <strong>{{ currentMonth }}</strong><br>
          Будут сгенерированы маршруты для всех активных сотрудников на основе категорий ТТ.
        </p>
        <!-- Праздники месяца -->
        <div v-if="monthHolidays.length > 0" class="mb-4">
          <p class="text-xs text-gray-500 mb-2">Нерабочие праздничные дни месяца:</p>
          <div class="space-y-1 max-h-40 overflow-y-auto">
            <label
              v-for="h in monthHolidays"
              :key="h.date"
              class="flex items-center gap-2 text-sm cursor-pointer"
            >
              <input
                type="checkbox"
                :checked="!h.is_working"
                @change="toggleHoliday(h)"
                class="accent-blue-500"
              />
              <span :class="h.is_working ? 'line-through text-gray-400' : 'text-gray-800'">
                {{ h.date }} — {{ h.name }}
              </span>
            </label>
          </div>
          <p class="text-xs text-gray-500 mt-1">Снимите галочку, чтобы сделать день рабочим</p>
        </div>
        <div class="flex gap-3 justify-end">
          <button class="btn-secondary" @click="showGenerate = false">Отмена</button>
          <button class="btn-primary" :disabled="generating" @click="generatePlan()">
            {{ generating ? 'Генерация…' : 'Сгенерировать' }}
          </button>
        </div>
        <div v-if="genResult" class="mt-3 text-sm" :class="genResult.startsWith('Ошибка') ? 'text-red-600' : 'text-green-600'">
          {{ genResult }}
        </div>
        <div v-if="genCanForce" class="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-xs text-red-700 mb-2">
            План за этот месяц уже существует. Перегенерация удалит все запланированные, перенесённые и пропущенные визиты.
          </p>
          <button class="bg-red-600 hover:bg-red-700 text-white text-sm px-4 py-2 rounded font-medium" :disabled="generating" @click="generatePlan(true)">
            {{ generating ? 'Генерация…' : 'Перегенерировать план' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Модал: праздники года -->
    <div v-if="showHolidays" class="modal-overlay" @click.self="showHolidays = false">
      <div class="modal" style="max-width:480px">
        <h2 class="font-semibold text-lg mb-4 text-gray-900">Праздничные дни 2026</h2>
        <p class="text-xs text-gray-500 mb-3">
          Отмеченные дни считаются нерабочими. Снимите галочку, чтобы сделать день рабочим.
        </p>
        <div v-if="allHolidaysLoading" class="text-sm text-gray-500">Загрузка…</div>
        <div v-else class="space-y-1 max-h-96 overflow-y-auto">
          <label
            v-for="h in allHolidays"
            :key="h.date"
            class="flex items-center gap-2 text-sm cursor-pointer py-0.5"
          >
            <input
              type="checkbox"
              :checked="!h.is_working"
              @change="toggleHoliday(h)"
              class="accent-blue-500"
            />
            <span :class="h.is_working ? 'line-through text-gray-400' : 'text-gray-800'">
              {{ h.date }} — {{ h.name }}
            </span>
          </label>
        </div>
        <div v-if="holidayToggleMsg" class="mt-2 text-xs" :class="holidayToggleMsgError ? 'text-red-600' : 'text-blue-600'">
          {{ holidayToggleMsg }}
        </div>
        <div class="flex justify-end mt-4">
          <button class="btn-secondary" @click="showHolidays = false">Закрыть</button>
        </div>
      </div>
    </div>

    <!-- Модал: форс-мажор -->
    <div v-if="showFM" class="modal-overlay" @click.self="showFM = false">
      <div class="modal">
        <h2 class="font-semibold text-lg mb-4 text-gray-900">Форс-мажор</h2>
        <div class="space-y-3">
          <div>
            <label class="label">Тип</label>
            <select v-model="fm.type" class="input">
              <option value="illness">Болезнь</option>
              <option value="weather">Погодные условия</option>
              <option value="vehicle_breakdown">Неисправность ТС</option>
              <option value="other">Другое</option>
            </select>
          </div>
          <div>
            <label class="label">Сотрудник</label>
            <select v-model="fm.rep_id" class="input">
              <option v-for="r in reps" :key="r.id" :value="r.id">{{ r.name }}</option>
            </select>
          </div>
          <div>
            <label class="label">Дата инцидента</label>
            <input v-model="fm.event_date" type="date" class="input" />
          </div>
          <div>
            <label class="label">Описание</label>
            <textarea v-model="fm.description" class="input" rows="2" />
          </div>
          <div>
            <label class="label">Сотрудник вернётся в: <span class="text-xs text-gray-400 font-normal">(необязательно)</span></label>
            <input v-model="fm.return_time" type="time" class="input" />
            <p class="text-xs text-gray-500 mt-1">Если указано, перераспределятся только визиты после этого времени.</p>
          </div>
        </div>
        <div class="flex gap-3 justify-end mt-4">
          <button class="btn-secondary" @click="showFM = false">Отмена</button>
          <button class="btn-primary" :disabled="submittingFM" @click="submitFM">
            {{ submittingFM ? 'Обработка…' : 'Зафиксировать' }}
          </button>
        </div>
        <div v-if="fmResult" class="mt-3 text-sm text-green-600 whitespace-pre-line">{{ fmResult }}</div>
      </div>
    </div>

    <!-- Модал: детальный просмотр дня + LLM оптимизация -->
    <div v-if="showDayModal && selectedDayRoute" class="modal-overlay" @click.self="showDayModal = false">
      <div class="planner-modal">
        <div class="planner-modal__header">
          <div class="min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h2 class="font-semibold text-lg text-gray-900">{{ selectedDayRoute.rep_name }}</h2>
              <span
                class="text-xs px-2 py-0.5 rounded-full"
                :class="routeSourceBadgeClass(selectedDayRoute.route_source)"
              >
                {{ routeSourceLabel(selectedDayRoute.route_source) }}
              </span>
              <span v-if="selectedDayRoute.route_label" class="text-xs text-gray-500 truncate max-w-[18rem]">
                {{ selectedDayRoute.route_label }}
              </span>
            </div>
            <p class="text-sm text-gray-600 mt-1">
              {{ selectedDayRoute.date }} · {{ selectedDayRoute.total_tt }} ТТ · ~{{ selectedDayRoute.estimated_duration_hours }}ч
            </p>
            <p class="text-xs text-gray-500 mt-1">
              {{ activePlannerHint }}
            </p>
            <!-- Транспорт ТП -->
            <div class="flex items-center gap-2 mt-2 flex-wrap">
              <select v-model="dayTransportMode" class="input-sm" @change="void refreshDayRouteMetrics()">
                <option value="car">🚗 Автомобиль</option>
                <option value="taxi">🚕 Такси</option>
                <option value="bus">🚌 Автобус</option>
              </select>
              <select v-if="dayTransportMode === 'car'" v-model="dayVehicleId" class="input-sm" @change="void refreshDayRouteMetrics()">
                <option :value="null">— авто по умолч. —</option>
                <option v-for="v in vehicles" :key="v.id" :value="v.id">{{ v.name }}</option>
              </select>
            </div>
            <!-- Map export links -->
            <div v-if="mapLinks" class="flex items-center gap-2 mt-2 flex-wrap">
              <span class="text-xs text-gray-400">Открыть маршрут:</span>
              <a :href="mapLinks.yandex" target="_blank" rel="noopener" class="map-link-btn">
                <img src="https://yastatic.net/s3/front-maps-static/maps-front-maps/src/assets/favicon/favicon-32.png" class="w-4 h-4" alt="" />
                Яндекс
              </a>
              <a :href="mapLinks.google" target="_blank" rel="noopener" class="map-link-btn">
                <img src="https://www.gstatic.com/images/icons/material/apps/fonts/1x/catalog/v5/favicon.svg" class="w-4 h-4" alt="" />
                Google
              </a>
              <a :href="mapLinks.dgis" target="_blank" rel="noopener" class="map-link-btn">
                2ГИС
              </a>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="showRouteComparison"
              class="btn-secondary text-xs"
              @click="comparisonExpanded = !comparisonExpanded"
            >
              {{ comparisonExpanded ? 'Скрыть сравнение' : 'Показать сравнение' }}
            </button>
            <button class="btn-icon text-xs" @click="showDayModal = false">✕</button>
          </div>
        </div>

        <div
          v-if="dayRouteMessage"
          class="mb-4 text-sm rounded-xl px-4 py-3 border"
          :class="dayRouteBannerClass"
        >
          {{ dayRouteMessage }}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-5">
          <div class="planner-summary-card">
            <p class="planner-summary-card__label">Активный маршрут</p>
            <p class="planner-summary-card__value">{{ routeSourceLabel(selectedDayRoute.route_source) }}</p>
            <p class="planner-summary-card__hint">{{ formatRouteMetrics(currentRouteMetrics) }}</p>
          </div>
          <div class="planner-summary-card">
            <p class="planner-summary-card__label">Черновик</p>
            <p class="planner-summary-card__value">{{ draftStatusLabel }}</p>
            <p class="planner-summary-card__hint">{{ draftStatusHint }}</p>
          </div>
          <div class="planner-summary-card">
            <p class="planner-summary-card__label">Изменение</p>
            <p class="planner-summary-card__value">{{ draftDeltaHeadline }}</p>
            <p class="planner-summary-card__hint">{{ draftDeltaSubline }}</p>
          </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-[1.1fr_0.9fr] gap-5">
          <div class="space-y-4">
            <div class="border border-gray-200 rounded-xl p-4 bg-white shadow-sm">
              <div class="flex items-center justify-between gap-3 mb-3">
                <div>
                  <h3 class="text-sm font-semibold text-gray-900">Текущий маршрут дня</h3>
                  <p class="text-xs text-gray-500">
                    {{ selectedDayRoute.has_route_override ? 'Порядок уже применён в расписании.' : 'Пока используется базовый порядок из расписания.' }}
                  </p>
                </div>
                <span class="text-xs text-gray-500 whitespace-nowrap">
                  {{ formatRouteMetrics(currentRouteMetrics) }}
                </span>
              </div>

              <div class="space-y-0.5 mb-4 max-h-56 overflow-y-auto pr-1">
                <div
                  v-for="(v, i) in currentDayVisits"
                  :key="`${v.id}-current`"
                  class="flex items-center gap-2 text-sm py-1.5 border-b border-gray-100"
                >
                  <span class="text-gray-400 w-5 shrink-0">{{ i + 1 }}.</span>
                  <span :class="catColor(v.location_category ?? '?')" class="visit-chip shrink-0 text-white">
                    {{ v.location_category ?? '?' }}
                  </span>
                  <span class="flex-1 truncate text-xs text-gray-800">{{ v.location_name }}</span>
                  <span v-if="v.time_in" class="text-xs text-gray-500 shrink-0">
                    {{ v.time_in }}–{{ v.time_out ?? '?' }}
                    <span v-if="visitDuration(v)" class="text-green-600 ml-0.5">({{ visitDuration(v) }}м)</span>
                  </span>
                  <span class="text-xs shrink-0" :class="statusColor(v.status)">{{ statusLabel(v.status) }}</span>
                </div>
              </div>

              <div v-if="watchdogRoutePoints.length" class="mb-1">
                <!-- Watch-dog панель прогресса -->
                <div class="flex items-center gap-3 mb-2 text-sm flex-wrap">
                  <span class="text-gray-600">
                    Осталось: <strong class="text-blue-700">{{ remainingVisitsCount }}</strong>
                  </span>
                  <button
                    class="btn-icon text-xs px-2 py-1 border border-gray-200 rounded hover:bg-gray-50"
                    :disabled="watchdogLoading"
                    :title="watchdogLoading ? 'Обновление…' : 'Обновить статусы'"
                    @click="refreshDayProgress"
                  >
                    <span :class="watchdogLoading ? 'animate-spin inline-block' : ''">↻</span>
                  </button>
                  <button
                    v-if="remainingVisitsCount > 0"
                    class="btn-secondary text-xs"
                    :disabled="dayOptLoading"
                    @click="optimizeRemainingVisits"
                  >
                    Оптимизировать оставшиеся ({{ remainingVisitsCount }})
                  </button>
                </div>
                <RouteMap :points="watchdogRoutePoints" height="20rem" />
                <!-- Легенда -->
                <div class="flex gap-4 text-xs text-gray-500 mt-2 flex-wrap">
                  <span class="flex items-center gap-1">
                    <span class="inline-block w-3 h-3 rounded-full bg-green-600" />выполнен
                  </span>
                  <span class="flex items-center gap-1">
                    <span class="inline-block w-3 h-3 rounded-full bg-red-700" />пропущен
                  </span>
                  <span class="flex items-center gap-1">
                    <span class="inline-block w-3 h-3 rounded-full bg-blue-500" />запланирован
                  </span>
                  <span class="flex items-center gap-1">
                    <span class="inline-block w-3 h-3 rounded-full bg-amber-500" />перенесён
                  </span>
                </div>
              </div>
            </div>

            <div
              v-if="showRouteComparison && comparisonExpanded"
              class="border border-blue-200 rounded-xl p-4 bg-blue-50/50"
            >
              <div class="flex items-center justify-between gap-3 mb-3">
                <div>
                  <h3 class="text-sm font-semibold text-gray-900">Сравнение маршрутов</h3>
                  <p class="text-xs text-gray-500">
                    {{ isDraftDirty ? 'Слева активный маршрут, справа ваш черновик.' : 'Слева исходный маршрут, справа применённый.' }}
                  </p>
                </div>
                <span v-if="previewLoading" class="text-xs text-gray-500">Пересчитываю метрики…</span>
              </div>

              <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div class="bg-white border border-gray-200 rounded-xl p-3">
                  <p class="text-xs font-semibold text-gray-700 mb-1">{{ comparisonLeftLabel }}</p>
                  <p class="text-xs text-gray-500 mb-2">{{ formatRouteMetrics(comparisonLeftMetrics) }}</p>
                  <div class="space-y-1 mb-3 max-h-40 overflow-y-auto">
                    <div
                      v-for="(visit, index) in comparisonLeftVisits"
                      :key="`${visit.id}-left-${index}`"
                      class="flex items-center gap-2 text-xs"
                    >
                      <span class="text-gray-400 w-4">{{ index + 1 }}</span>
                      <span :class="catColor(visit.location_category ?? '?')" class="visit-chip shrink-0 text-white">
                        {{ visit.location_category ?? '?' }}
                      </span>
                      <span class="truncate text-gray-800">{{ visit.location_name }}</span>
                    </div>
                  </div>
                  <RouteMap v-if="comparisonLeftPoints.length >= 2" :points="comparisonLeftPoints" height="14rem" />
                </div>

                <div class="bg-white border border-gray-200 rounded-xl p-3">
                  <p class="text-xs font-semibold text-gray-700 mb-1">{{ comparisonRightLabel }}</p>
                  <p class="text-xs text-gray-500 mb-2">{{ formatRouteMetrics(comparisonRightMetrics) }}</p>
                  <div class="space-y-1 mb-3 max-h-40 overflow-y-auto">
                    <div
                      v-for="(visit, index) in comparisonRightVisits"
                      :key="`${visit.id}-right-${index}`"
                      class="flex items-center gap-2 text-xs"
                    >
                      <span class="text-gray-400 w-4">{{ index + 1 }}</span>
                      <span :class="catColor(visit.location_category ?? '?')" class="visit-chip shrink-0 text-white">
                        {{ visit.location_category ?? '?' }}
                      </span>
                      <span class="truncate text-gray-800">{{ visit.location_name }}</span>
                    </div>
                  </div>
                  <RouteMap v-if="comparisonRightPoints.length >= 2" :points="comparisonRightPoints" height="14rem" />
                </div>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="border border-gray-200 rounded-xl p-4 bg-white shadow-sm">
              <div class="flex items-center gap-2 mb-4">
                <button
                  class="planner-tab flex-1"
                  :class="plannerPanel === 'draft' ? 'planner-tab--active' : ''"
                  @click="plannerPanel = 'draft'"
                >
                  Редактор
                </button>
                <button
                  class="planner-tab flex-1"
                  :class="plannerPanel === 'ai' ? 'planner-tab--active' : ''"
                  @click="plannerPanel = 'ai'"
                >
                  Варианты ИИ
                </button>
              </div>

              <div v-if="plannerPanel === 'draft'" class="space-y-4">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <h3 class="text-sm font-semibold text-gray-900">Черновик маршрута</h3>
                  <p class="text-xs text-gray-500">
                    Перетаскивайте точки или используйте стрелки. Изменения считаются сразу.
                  </p>
                </div>
                <span class="text-xs text-gray-500 text-right">
                  {{ isDraftDirty ? formatRouteMetrics(draftRouteMetrics) : 'Совпадает с текущим' }}
                </span>
              </div>

              <div class="space-y-2 max-h-72 overflow-y-auto pr-1">
                <div
                  v-for="(visit, index) in draftDayVisits"
                  :key="`${visit.id}-draft-${index}`"
                  class="planner-route-row"
                  :class="draftDragOverIndex === index ? 'planner-route-row--drag' : ''"
                  :draggable="!previewLoading"
                  @dragstart="onDraftDragStart(index, $event)"
                  @dragenter.prevent="onDraftDragEnter(index)"
                  @dragover.prevent="onDraftDragEnter(index)"
                  @drop.prevent="onDraftDrop(index)"
                  @dragend="onDraftDragEnd"
                >
                  <span class="text-gray-400 w-4 text-xs">{{ index + 1 }}</span>
                  <span class="planner-drag-handle" title="Перетащить точку">⋮⋮</span>
                  <span :class="catColor(visit.location_category ?? '?')" class="visit-chip shrink-0 text-white">
                    {{ visit.location_category ?? '?' }}
                  </span>
                  <span class="flex-1 truncate text-xs text-gray-800">{{ visit.location_name }}</span>
                  <div class="flex items-center gap-1">
                    <button class="btn-icon text-xs !w-7 !h-7" :disabled="index === 0" @click="moveDraftPoint(index, -1)">↑</button>
                    <button class="btn-icon text-xs !w-7 !h-7" :disabled="index === draftDayVisits.length - 1" @click="moveDraftPoint(index, 1)">↓</button>
                  </div>
                </div>
              </div>

              <div class="planner-action-bar">
                <button
                  class="btn-secondary text-xs"
                  :disabled="!isDraftDirty"
                  @click="resetDraftToCurrent"
                >
                  Сбросить
                </button>
                <button
                  v-if="selectedDayRoute.has_route_override"
                  class="btn-secondary text-xs"
                  :disabled="revertingDayRoute"
                  @click="revertAppliedRoute"
                >
                  {{ revertingDayRoute ? 'Откат…' : 'Откатить' }}
                </button>
                <button
                  class="btn-primary text-xs"
                  :disabled="!isDraftDirty || confirmingVariant"
                  @click="applyDraftRoute"
                >
                  {{ confirmingVariant ? 'Применение…' : 'Применить маршрут' }}
                </button>
              </div>
              </div>

              <div v-else class="space-y-4">
                <div class="mb-4">
                  <h3 class="text-sm font-semibold text-gray-900">Варианты от ИИ</h3>
                  <p class="text-xs text-gray-500 mt-1">
                    Получите 3 варианта и нажмите по карточке, чтобы открыть его в черновике.
                  </p>
                </div>

            <!-- Выбор модели + кнопка оптимизации -->
            <div class="border border-gray-200 rounded-xl p-3 bg-gray-50 mb-4">
              <p class="text-xs text-gray-500 mb-2">Модель для оценки вариантов</p>
              <div class="flex gap-2 mb-3">
                <button
                  v-for="m in [{ id: 'qwen', label: 'Qwen 0.5B', hint: 'быстрая' }, { id: 'llama', label: 'Llama 1B', hint: 'точнее' }]"
                  :key="m.id"
                  class="flex-1 text-xs py-2 rounded-lg font-medium transition-colors border"
                  :class="selectedModel === m.id
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'"
                  :disabled="dayOptLoading"
                  @click="selectedModel = (m.id as 'qwen' | 'llama')"
                >
                  {{ m.label }}
                  <span class="opacity-60 ml-1">({{ m.hint }})</span>
                </button>
              </div>

              <button
                class="btn-primary w-full flex items-center justify-center gap-2"
                :disabled="dayOptLoading"
                @click="optimizeDayRoute"
              >
                <svg v-if="dayOptLoading" class="animate-spin h-4 w-4 text-white flex-shrink-0" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>{{ dayOptLoading ? 'Строю варианты…' : 'Получить 3 варианта' }}</span>
              </button>

              <!-- Прогресс-бар -->
              <div v-if="dayOptLoading" class="mt-2">
                <div class="relative w-full bg-gray-200 rounded-full h-1 overflow-hidden">
                  <div class="absolute top-0 left-0 h-1 bg-blue-500 rounded-full animate-pulse w-full" />
                </div>
                <p class="text-xs text-gray-500 mt-1 text-center">
                  Оцениваю маршрут через {{ selectedModel === 'qwen' ? 'Qwen' : 'Llama' }}…
                </p>
              </div>
            </div>

            <div v-if="dayOptError" class="mb-3 text-sm text-red-600">{{ dayOptError }}</div>

            <!-- 3 варианта маршрута -->
            <div v-if="dayOptResult" class="space-y-2">
              <div class="flex items-center justify-between gap-2 text-xs text-gray-500 mb-2">
                <span>{{ dayOptResult.variants.length }} варианта готовы</span>
                <span>
                  Модель: <strong class="text-blue-700">{{ dayOptResult.model_used }}</strong>
                  <span v-if="!dayOptResult.llm_evaluation_success" class="text-yellow-600 ml-1">· ИИ-оценка недоступна</span>
                </span>
              </div>

              <div
                v-for="variant in dayOptResult.variants"
                :key="variant.id"
                class="rounded-xl border p-3 cursor-pointer transition-all"
                :class="selectedVariantId === variant.id
                  ? 'border-blue-500 bg-blue-50 shadow-sm'
                  : 'border-gray-200 bg-gray-50 hover:border-gray-300'"
                @click="previewVariant(variant)"
              >
                <div class="flex items-start justify-between mb-1 gap-3">
                  <div>
                    <p class="text-sm font-medium text-gray-900">{{ variant.name }}</p>
                    <p class="text-xs text-gray-600 mt-0.5">{{ variant.description }}</p>
                  </div>
                  <span class="text-xs px-1.5 py-0.5 rounded ml-2 flex-shrink-0"
                    :class="variant.metrics.quality_score >= 80 ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-700'"
                  >
                    {{ variant.metrics.quality_score.toFixed(0) }}%
                  </span>
                </div>
                <div class="flex flex-wrap gap-3 text-xs text-gray-700 mb-2">
                  <span>📍 {{ variant.metrics.distance_km.toFixed(1) }} км</span>
                  <span>⏱ {{ variant.metrics.time_hours.toFixed(1) }} ч</span>
                  <span>💰 {{ variant.metrics.cost_rub.toFixed(0) }} ₽</span>
                </div>
                <div v-if="variant.pros.length || variant.cons.length" class="flex flex-wrap gap-1">
                  <span
                    v-for="p in variant.pros" :key="'p'+p"
                    class="text-xs bg-green-100 text-green-800 px-1.5 py-0.5 rounded"
                  >✓ {{ p }}</span>
                  <span
                    v-for="c in variant.cons" :key="'c'+c"
                    class="text-xs bg-red-100 text-red-800 px-1.5 py-0.5 rounded"
                  >✗ {{ c }}</span>
                </div>
              </div>
            </div>

            <div v-else class="planner-empty-state">
              Вариантов пока нет. Сначала нажмите «Получить 3 варианта».
            </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модал: статус визита -->
    <div v-if="showVisitModal && selectedVisit" class="modal-overlay" @click.self="closeVisitModal">
      <div class="modal">
        <h2 class="font-semibold text-lg mb-1 text-gray-900">Визит</h2>
        <p class="text-sm text-gray-700 mb-4">
          <span :class="catBadge(selectedVisit.location_category)" class="visit-chip mr-2">
            {{ selectedVisit.location_category ?? '?' }}
          </span>
          {{ selectedVisit.location_name }}
        </p>

        <!-- Сохранённое время (если уже было посещение) -->
        <p v-if="selectedVisit?.time_in" class="text-sm text-blue-700 mb-3">
          ⏱ {{ selectedVisit.time_in }} — {{ selectedVisit.time_out ?? '?' }}
          <span v-if="visitDuration(selectedVisit!)" class="ml-1 text-green-600">
            ({{ visitDuration(selectedVisit!) }} мин на точке)
          </span>
        </p>

        <!-- Кнопки статуса -->
        <div class="flex gap-2 mb-4">
          <button
            v-for="opt in statusOptions"
            :key="opt.value"
            :class="[opt.cls, visitForm.status === opt.value ? 'ring-2 ring-blue-500' : 'opacity-80']"
            class="flex-1 text-sm py-1.5 rounded font-medium"
            @click="visitForm.status = opt.value"
          >
            {{ opt.label }}
          </button>
        </div>

        <!-- Время (только для выполненного) -->
        <div v-if="visitForm.status === 'completed'" class="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label class="label">Прибыл в</label>
            <input v-model="visitForm.time_in" type="time" class="input" />
          </div>
          <div>
            <label class="label">Ушёл в</label>
            <input v-model="visitForm.time_out" type="time" class="input" />
          </div>
        </div>

        <!-- Заметки -->
        <div class="mb-4">
          <label class="label">Заметки</label>
          <textarea v-model="visitForm.notes" class="input" rows="2"
            placeholder="Причина пропуска, комментарий…" />
        </div>

        <div class="flex gap-3 justify-end">
          <button class="btn-secondary" @click="closeVisitModal">Отмена</button>
          <button class="btn-primary" :disabled="savingVisit" @click="submitVisitUpdate">
            {{ savingVisit ? 'Сохранение…' : 'Сохранить' }}
          </button>
        </div>
        <div v-if="visitError" class="mt-2 text-sm text-red-600">{{ visitError }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import PageHero from '@/components/common/PageHero.vue'
import type {
  DailyRoute,
  Holiday,
  Location,
  OptimizeVariantsResponse,
  ConfirmVariantRequest,
  SalesRep,
  SkippedStashItem,
  VisitScheduleItem,
  RouteVariant,
  Vehicle,
  TransportMode,
} from '@/services/types'
import {
  optimizeVariants,
  confirmVariant,
  fetchRoutePreview,
  updateVisitStatus,
  downloadScheduleExcel,
  fetchMonthlySchedule,
  fetchReps,
  generateSchedule,
  createForceMajeure,
  fetchHolidays,
  patchHoliday,
  fetchAllLocations,
  saveDayRouteOverride,
  revertDayRouteOverride,
  fetchDailySchedule,
  fetchSkippedStash,
  resolveStashManual,
  resolveStashCarryOver,
  resolveStashAI,
  discardStashEntry,
  fetchVehicles,
} from '@/services/api'
import RouteMap, { type RoutePoint } from '@/components/RouteMap.vue'

// ─── State ───────────────────────────────────────────────────────────────────
const today = new Date()
const savedOffset = parseInt(localStorage.getItem('t2_month_offset') ?? '0', 10)
const monthOffset = ref(isNaN(savedOffset) ? 0 : savedOffset)
watch(monthOffset, (v) => localStorage.setItem('t2_month_offset', String(v)))
const routes = ref<DailyRoute[]>([])
const reps = ref<SalesRep[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showGenerate = ref(false)
const showFM = ref(false)
const showHolidays = ref(false)
const exportLoading = ref(false)
const generating = ref(false)
const genResult = ref<string | null>(null)
const genCanForce = ref(false)
const submittingFM = ref(false)
const fmResult = ref<string | null>(null)

// ─── Holidays state ───────────────────────────────────────────────────────────
const monthHolidays = ref<Holiday[]>([])
const allHolidays = ref<Holiday[]>([])
const allHolidaysLoading = ref(false)
const holidayToggleMsg = ref<string | null>(null)
const holidayToggleMsgError = ref(false)

// ─── Visit modal state ────────────────────────────────────────────────────────
const showVisitModal = ref(false)
const selectedVisit = ref<VisitScheduleItem | null>(null)
const savingVisit = ref(false)
const visitError = ref<string | null>(null)
const visitForm = ref({
  status: 'planned' as VisitScheduleItem['status'],
  time_in: '',
  time_out: '',
  notes: '',
})

const statusOptions = [
  { value: 'completed' as const, label: '✓ Выполнен', cls: 'bg-green-700 hover:bg-green-600' },
  { value: 'skipped' as const,   label: '✗ Пропущен',  cls: 'bg-red-700 hover:bg-red-600' },
  { value: 'planned' as const,   label: '⏳ Запланирован', cls: 'bg-gray-600 hover:bg-gray-500' },
]

// ─── Day detail modal state ───────────────────────────────────────────────────
const showDayModal = ref(false)
const selectedDayRoute = ref<DailyRoute | null>(null)
const dayOptResult = ref<OptimizeVariantsResponse | null>(null)
const dayOptLoading = ref(false)
const dayOptError = ref<string | null>(null)
const selectedModel = ref<'qwen' | 'llama'>('qwen')
const selectedVariantId = ref<number | null>(null)
const confirmingVariant = ref(false)
const revertingDayRoute = ref(false)
const draftLocationIds = ref<string[]>([])
const draftRouteSource = ref<'generated' | 'ai' | 'manual'>('generated')
const draftRouteLabel = ref<string | null>(null)
const dayRouteMessage = ref<string | null>(null)
const dayRouteMessageTone = ref<'success' | 'info' | 'warning'>('success')
const previewLoading = ref(false)
const originalRouteMetrics = ref<RouteMetrics | null>(null)
const currentRouteMetrics = ref<RouteMetrics | null>(null)
const draftRouteMetrics = ref<RouteMetrics | null>(null)
const vehicles = ref<Vehicle[]>([])
const dayTransportMode = ref<TransportMode>('car')
const dayVehicleId = ref<string | null>(null)
const plannerPanel = ref<'draft' | 'ai'>('draft')
const comparisonExpanded = ref(false)
const draftDragFromIndex = ref<number | null>(null)
const draftDragOverIndex = ref<number | null>(null)

const fm = ref({
  type: 'illness' as string,
  rep_id: '',
  event_date: '',
  description: '',
  return_time: '',
})

interface RouteMetrics {
  distance_km: number
  time_hours: number
  cost_rub: number
}

// ─── Computed ─────────────────────────────────────────────────────────────────
const currentMonth = computed(() => {
  const d = new Date(today.getFullYear(), today.getMonth() + monthOffset.value, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
})

const monthLabel = computed(() => {
  const [y, m] = currentMonth.value.split('-')
  const names = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                 'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
  return `${names[Number(m) - 1]} ${y}`
})

// Locations cache for joining visits → coordinates (used by RouteMap in day modal)
const locationsById = ref<Map<string, Location>>(new Map())

const currentLocationIds = computed<string[]>(() => {
  if (!selectedDayRoute.value) return []
  if (selectedDayRoute.value.current_location_ids?.length) {
    return [...selectedDayRoute.value.current_location_ids]
  }
  return selectedDayRoute.value.visits.map((visit) => visit.location_id)
})

const originalLocationIds = computed<string[]>(() => {
  if (!selectedDayRoute.value) return []
  if (selectedDayRoute.value.original_location_ids?.length) {
    return [...selectedDayRoute.value.original_location_ids]
  }
  return currentLocationIds.value
})

const isDraftDirty = computed(() =>
  !isSameLocationOrder(draftLocationIds.value, currentLocationIds.value)
)

const selectedVariant = computed<RouteVariant | null>(() => {
  if (!dayOptResult.value || selectedVariantId.value === null) return null
  return dayOptResult.value.variants.find((variant) => variant.id === selectedVariantId.value) ?? null
})

const currentDayVisits = computed(() => getVisitsByLocationOrder(currentLocationIds.value))
const originalDayVisits = computed(() => getVisitsByLocationOrder(originalLocationIds.value))

// ─── Map links for current day route ──────────────────────────────────────────
const mapLinks = computed(() => {
  const points = currentLocationIds.value
    .map(id => locationsById.value.get(id))
    .filter((loc): loc is Location => !!loc && typeof loc.lat === 'number' && typeof loc.lon === 'number')
  if (points.length < 2) return null
  const yandexParts = points.map(p => `${p.lat},${p.lon}`).join('~')
  const googleParts = points.map(p => `${p.lat},${p.lon}`).join('/')
  const dgisFirst = points[0]
  const dgisLast = points[points.length - 1]
  return {
    yandex: `https://yandex.ru/maps/?rtext=${yandexParts}&rtt=auto`,
    google: `https://www.google.com/maps/dir/${googleParts}/`,
    dgis: `https://2gis.ru/directions/points/${dgisFirst.lon},${dgisFirst.lat}/${dgisLast.lon},${dgisLast.lat}`,
  }
})
const draftDayVisits = computed(() =>
  getVisitsByLocationOrder(isDraftDirty.value ? draftLocationIds.value : currentLocationIds.value)
)

const currentRoutePoints = computed<RoutePoint[]>(() => buildRoutePoints(currentLocationIds.value))
const originalRoutePoints = computed<RoutePoint[]>(() => buildRoutePoints(originalLocationIds.value))

// ─── Watch-dog: прогресс дня ──────────────────────────────────────────────────
const STATUS_COLORS: Record<string, string> = {
  completed:   '#16a34a',
  skipped:     '#b91c1c',
  cancelled:   '#9ca3af',
  planned:     '#3b82f6',
  rescheduled: '#f59e0b',
}
const watchdogLoading = ref(false)
const liveVisitStatuses = ref(new Map<string, string>())

const remainingVisitsCount = computed(() =>
  currentDayVisits.value.filter(
    (v) => (liveVisitStatuses.value.get(v.id) ?? v.status) === 'planned'
  ).length
)

const watchdogRoutePoints = computed<RoutePoint[]>(() =>
  buildRoutePoints(currentLocationIds.value).map((p) => {
    const visit = currentDayVisits.value.find((v) => v.id === p.id)
    const status = visit
      ? (liveVisitStatuses.value.get(visit.id) ?? visit.status)
      : 'planned'
    return { ...p, color: STATUS_COLORS[status] ?? '#3b82f6' }
  })
)

async function refreshDayProgress() {
  if (!selectedDayRoute.value) return
  watchdogLoading.value = true
  try {
    const daily = await fetchDailySchedule(selectedDayRoute.value.date)
    const repRoute = daily.find((r) => r.rep_id === selectedDayRoute.value!.rep_id)
    if (repRoute) {
      liveVisitStatuses.value = new Map(repRoute.visits.map((v) => [v.id, v.status]))
    }
  } catch {
    // не мешаем работе модала при ошибке обновления
  } finally {
    watchdogLoading.value = false
  }
}

async function optimizeRemainingVisits() {
  if (!selectedDayRoute.value) return
  const ids = currentDayVisits.value
    .filter((v) => (liveVisitStatuses.value.get(v.id) ?? v.status) === 'planned')
    .map((v) => v.location_id)
  if (!ids.length) return
  plannerPanel.value = 'ai'
  dayOptLoading.value = true
  dayOptError.value = null
  dayOptResult.value = null
  selectedVariantId.value = null
  try {
    dayOptResult.value = await optimizeVariants(ids, selectedModel.value, {})
  } catch (e: any) {
    dayOptError.value = e?.message ?? 'Ошибка оптимизации'
  } finally {
    dayOptLoading.value = false
  }
}
// ─── Стеш пропущенных визитов ─────────────────────────────────────────────────
const skippedStash = ref<SkippedStashItem[]>([])
const stashModalEntry = ref<SkippedStashItem | null>(null)
const stashManualRepId = ref('')
const stashManualDate = ref('')
const stashLoading = ref(false)

async function loadSkippedStash() {
  try {
    skippedStash.value = await fetchSkippedStash()
  } catch {
    // не блокируем интерфейс при ошибке загрузки
  }
}

function openStashModal(entry: SkippedStashItem) {
  stashModalEntry.value = entry
  stashManualRepId.value = entry.rep_id
  stashManualDate.value = ''
}

async function resolveCarryOver(id: string) {
  stashLoading.value = true
  try {
    await resolveStashCarryOver(id)
    await loadSkippedStash()
    await loadSchedule()
  } catch (e: any) {
    alert(`Ошибка переноса: ${e?.message ?? 'неизвестная'}`)
  } finally {
    stashLoading.value = false
  }
}

async function submitStashManual() {
  if (!stashModalEntry.value || !stashManualRepId.value || !stashManualDate.value) return
  stashLoading.value = true
  try {
    await resolveStashManual(stashModalEntry.value.id, stashManualRepId.value, stashManualDate.value)
    stashModalEntry.value = null
    await loadSkippedStash()
    await loadSchedule()
  } catch (e: any) {
    alert(`Ошибка назначения: ${e?.message ?? 'неизвестная'}`)
  } finally {
    stashLoading.value = false
  }
}

async function resolveAllAI() {
  const ids = skippedStash.value.map((e) => e.id)
  if (!ids.length) return
  stashLoading.value = true
  try {
    await resolveStashAI(ids)
    await loadSkippedStash()
    await loadSchedule()
  } catch (e: any) {
    alert(`Ошибка ИИ-перераспределения: ${e?.message ?? 'неизвестная'}`)
  } finally {
    stashLoading.value = false
  }
}

async function discardStash(id: string) {
  stashLoading.value = true
  try {
    await discardStashEntry(id)
    await loadSkippedStash()
  } catch (e: any) {
    alert(`Ошибка: ${e?.message ?? 'неизвестная'}`)
  } finally {
    stashLoading.value = false
  }
}

const draftRoutePoints = computed<RoutePoint[]>(() =>
  buildRoutePoints(isDraftDirty.value ? draftLocationIds.value : currentLocationIds.value)
)

const showRouteComparison = computed(() => {
  if (!selectedDayRoute.value) return false
  if (isDraftDirty.value) return true
  return !isSameLocationOrder(originalLocationIds.value, currentLocationIds.value)
})

const comparisonLeftLabel = computed(() =>
  isDraftDirty.value ? 'Текущий' : 'Исходный'
)

const comparisonRightLabel = computed(() =>
  isDraftDirty.value ? 'Предпросмотр' : 'Текущий'
)

const comparisonLeftVisits = computed(() =>
  isDraftDirty.value ? currentDayVisits.value : originalDayVisits.value
)

const comparisonRightVisits = computed(() =>
  isDraftDirty.value ? draftDayVisits.value : currentDayVisits.value
)

const comparisonLeftPoints = computed(() =>
  isDraftDirty.value ? currentRoutePoints.value : originalRoutePoints.value
)

const comparisonRightPoints = computed(() =>
  isDraftDirty.value ? draftRoutePoints.value : currentRoutePoints.value
)

const comparisonLeftMetrics = computed(() =>
  isDraftDirty.value ? currentRouteMetrics.value : originalRouteMetrics.value
)

const comparisonRightMetrics = computed(() =>
  isDraftDirty.value ? draftRouteMetrics.value : currentRouteMetrics.value
)

const draftStatusLabel = computed(() =>
  isDraftDirty.value ? 'Есть изменения' : 'Без изменений'
)

const draftStatusHint = computed(() => {
  if (selectedVariant.value) {
    return `Предпросмотр: ${selectedVariant.value.name}`
  }
  if (draftRouteSource.value === 'manual' && isDraftDirty.value) {
    return 'Порядок изменён вручную'
  }
  return isDraftDirty.value ? 'Черновик отличается от активного маршрута' : 'Черновик совпадает с активным маршрутом'
})

const draftDeltaHeadline = computed(() => {
  if (!isDraftDirty.value || !currentRouteMetrics.value || !draftRouteMetrics.value) return 'Без разницы'
  const distanceDelta = draftRouteMetrics.value.distance_km - currentRouteMetrics.value.distance_km
  if (Math.abs(distanceDelta) < 0.05) return 'Почти без изменений'
  return `${distanceDelta < 0 ? 'Меньше' : 'Больше'} на ${Math.abs(distanceDelta).toFixed(1)} км`
})

const draftDeltaSubline = computed(() => {
  if (!isDraftDirty.value || !currentRouteMetrics.value || !draftRouteMetrics.value) {
    return 'Метрики совпадают с активным маршрутом'
  }
  return `${formatDelta(currentRouteMetrics.value.time_hours, draftRouteMetrics.value.time_hours, 'ч')} · ${formatDelta(currentRouteMetrics.value.cost_rub, draftRouteMetrics.value.cost_rub, '₽', 0)}`
})

const activePlannerHint = computed(() => {
  if (!selectedDayRoute.value) return ''
  const sourceText = selectedDayRoute.value.has_route_override ? 'сейчас действует изменённый маршрут' : 'сейчас действует базовый маршрут'
  return `${sourceText}; текущие метрики: ${formatRouteMetrics(currentRouteMetrics.value)}`
})

const dayRouteBannerClass = computed(() => {
  if (dayRouteMessageTone.value === 'warning') {
    return 'text-amber-800 bg-amber-50 border-amber-200'
  }
  if (dayRouteMessageTone.value === 'info') {
    return 'text-blue-800 bg-blue-50 border-blue-200'
  }
  return 'text-green-700 bg-green-50 border-green-200'
})

const sortedRoutes = computed(() =>
  [...routes.value].sort((a, b) => a.date.localeCompare(b.date) || a.rep_name.localeCompare(b.rep_name))
)

function isSameLocationOrder(a: string[], b: string[]): boolean {
  return a.length === b.length && a.every((value, index) => value === b[index])
}

function getVisitLookup() {
  return new Map(
    (selectedDayRoute.value?.visits ?? []).map((visit) => [visit.location_id, visit])
  )
}

function getVisitsByLocationOrder(locationIds: string[]): VisitScheduleItem[] {
  const visitLookup = getVisitLookup()
  return locationIds
    .map((locationId) => visitLookup.get(locationId))
    .filter((visit): visit is VisitScheduleItem => !!visit)
}

function buildRoutePoints(locationIds: string[]): RoutePoint[] {
  const visitLookup = getVisitLookup()
  const points: RoutePoint[] = []

  locationIds.forEach((locationId, index) => {
    const visit = visitLookup.get(locationId)
    const location = locationsById.value.get(locationId)
    if (!visit || !location) {
      if (import.meta.env.DEV) console.warn('RouteMap: location not found for visit', locationId)
      return
    }
    points.push({
      id: visit.id,
      name: visit.location_name,
      address: location.address,
      lat: location.lat,
      lon: location.lon,
      order: index + 1,
    })
  })

  return points
}

async function getRouteMetricsForLocationIds(locationIds: string[]): Promise<RouteMetrics> {
  const points = locationIds
    .map((locationId) => locationsById.value.get(locationId))
    .filter((location): location is Location => !!location)
    .map((location) => ({
      lat: location.lat,
      lon: location.lon,
    }))

  if (points.length < 2) {
    return {
      distance_km: 0,
      time_hours: 0,
      cost_rub: 0,
    }
  }

  const preview = await fetchRoutePreview(points, {
    vehicle_id: dayVehicleId.value,
    transport_mode: dayTransportMode.value,
  })
  return {
    distance_km: preview.distance_km,
    time_hours: preview.time_minutes / 60,
    cost_rub: preview.cost_rub,
  }
}

async function refreshDayRouteMetrics() {
  if (!selectedDayRoute.value) return

  previewLoading.value = true
  try {
    originalRouteMetrics.value = await getRouteMetricsForLocationIds(originalLocationIds.value)
    currentRouteMetrics.value = await getRouteMetricsForLocationIds(currentLocationIds.value)
    draftRouteMetrics.value = isDraftDirty.value
      ? await getRouteMetricsForLocationIds(draftLocationIds.value)
      : null
  } catch (e: any) {
    dayOptError.value = e?.message ?? 'Не удалось пересчитать метрики маршрута'
  } finally {
    previewLoading.value = false
  }
}

function routeSourceLabel(source?: DailyRoute['route_source']): string {
  if (source === 'ai') return 'ИИ'
  if (source === 'manual') return 'Ручной'
  return 'Базовый'
}

function routeSourceBadgeClass(source?: DailyRoute['route_source']): string {
  if (source === 'ai') return 'bg-blue-100 text-blue-700'
  if (source === 'manual') return 'bg-amber-100 text-amber-700'
  return 'bg-gray-100 text-gray-600'
}

function formatRouteMetrics(metrics: RouteMetrics | null): string {
  if (!metrics) return '—'
  return `${metrics.distance_km.toFixed(1)} км · ${metrics.time_hours.toFixed(1)} ч · ${metrics.cost_rub.toFixed(0)} ₽`
}

function formatDelta(currentValue: number, nextValue: number, unit: string, digits = 1): string {
  const delta = nextValue - currentValue
  if (Math.abs(delta) < (digits === 0 ? 0.5 : 0.05)) return `±0 ${unit}`
  const sign = delta < 0 ? '−' : '+'
  return `${sign}${Math.abs(delta).toFixed(digits)} ${unit}`
}

function setDayRouteMessage(message: string | null, tone: 'success' | 'info' | 'warning' = 'success') {
  dayRouteMessage.value = message
  dayRouteMessageTone.value = tone
}

function updateRouteInState(updatedRoute: DailyRoute) {
  const routeIndex = routes.value.findIndex(
    (route) => route.rep_id === updatedRoute.rep_id && route.date === updatedRoute.date
  )
  if (routeIndex !== -1) {
    routes.value.splice(routeIndex, 1, updatedRoute)
  }

  if (
    selectedDayRoute.value &&
    selectedDayRoute.value.rep_id === updatedRoute.rep_id &&
    selectedDayRoute.value.date === updatedRoute.date
  ) {
    selectedDayRoute.value = updatedRoute
  }
}

// ─── Methods ──────────────────────────────────────────────────────────────────
function shiftMonth(delta: number) {
  monthOffset.value += delta
  loadSchedule()
}

async function loadSchedule() {
  loading.value = true
  error.value = null
  try {
    const plan = await fetchMonthlySchedule(currentMonth.value)
    routes.value = plan.routes ?? []
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function loadReps() {
  reps.value = await fetchReps().catch(() => [])
}

async function openGenerateModal() {
  showGenerate.value = true
  genResult.value = null
  genCanForce.value = false
  monthHolidays.value = await fetchHolidays({ month: currentMonth.value }).catch(() => [])
}

async function toggleHoliday(h: Holiday) {
  const newIsWorking = !h.is_working
  try {
    const result = await patchHoliday(h.date, newIsWorking)
    h.is_working = result.is_working
    // Синхронизируем в обоих списках
    const inAll = allHolidays.value.find(x => x.date === h.date)
    if (inAll) inAll.is_working = result.is_working
    const inMonth = monthHolidays.value.find(x => x.date === h.date)
    if (inMonth) inMonth.is_working = result.is_working

    if (!newIsWorking && result.affected_visits_count > 0) {
      holidayToggleMsg.value = `На ${h.date} запланировано ${result.affected_visits_count} визитов — пересоздайте план для их переноса.`
      holidayToggleMsgError.value = true
    } else {
      holidayToggleMsg.value = `День ${h.date} теперь ${newIsWorking ? 'рабочий' : 'нерабочий'}.`
      holidayToggleMsgError.value = false
    }
    if (showDayModal.value && selectedDayRoute.value?.date === h.date) {
      void refreshDayRouteMetrics()
    }
  } catch (e: any) {
    holidayToggleMsg.value = `Ошибка: ${e?.message ?? e}`
    holidayToggleMsgError.value = true
  }
}

async function generatePlan(force = false) {
  generating.value = true
  genResult.value = null
  genCanForce.value = false
  try {
    const data = await generateSchedule(currentMonth.value, undefined, force)
    genResult.value = `Готово: ${data.total_visits_planned} визитов, охват ${data.coverage_pct}%`
    await loadSchedule()
  } catch (e: any) {
    const status = e?.response?.status
    const detail = e?.response?.data?.detail
    const msg = typeof detail === 'string'
      ? detail
      : detail?.message ?? e?.message ?? String(e)
    genResult.value = `Ошибка: ${msg}`
    if (status === 409) genCanForce.value = true
  } finally {
    generating.value = false
  }
}

async function submitFM() {
  submittingFM.value = true
  fmResult.value = null
  try {
    const data = await createForceMajeure({
      type: fm.value.type,
      rep_id: fm.value.rep_id,
      event_date: fm.value.event_date,
      description: fm.value.description || undefined,
      return_time: fm.value.return_time || undefined,
    })
    fmResult.value = `Зафиксировано. Перераспределено ${data.affected_tt_count} ТТ.`
    await loadSchedule()
  } catch (e: any) {
    fmResult.value = `Ошибка: ${e.message}`
  } finally {
    submittingFM.value = false
  }
}

// ─── Visit modal ──────────────────────────────────────────────────────────────
function openVisitModal(visit: VisitScheduleItem) {
  selectedVisit.value = visit
  visitForm.value = {
    status: visit.status,
    time_in: visit.time_in ?? '',
    time_out: visit.time_out ?? '',
    notes: '',
  }
  visitError.value = null
  showVisitModal.value = true
}

function closeVisitModal() {
  showVisitModal.value = false
  selectedVisit.value = null
}

async function submitVisitUpdate() {
  if (!selectedVisit.value) return
  savingVisit.value = true
  visitError.value = null
  try {
    const updated = await updateVisitStatus(selectedVisit.value.id, {
      status: visitForm.value.status,
      time_in: visitForm.value.time_in || undefined,
      time_out: visitForm.value.time_out || undefined,
      notes: visitForm.value.notes || undefined,
    })
    // Обновляем визит в локальном состоянии
    for (const route of routes.value) {
      const idx = route.visits.findIndex(v => v.id === updated.id)
      if (idx !== -1) {
        route.visits[idx] = updated
        break
      }
    }
    closeVisitModal()
    void loadSkippedStash()
    void refreshDayProgress()
  } catch (e: any) {
    visitError.value = e?.message ?? 'Ошибка сохранения'
  } finally {
    savingVisit.value = false
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function visitDuration(visit: VisitScheduleItem): number | null {
  if (!visit.time_in || !visit.time_out) return null
  const [h1, m1] = visit.time_in.split(':').map(Number)
  const [h2, m2] = visit.time_out.split(':').map(Number)
  const diff = (h2 * 60 + m2) - (h1 * 60 + m1)
  return diff > 0 ? diff : null
}

// ─── Экспорт в Excel ──────────────────────────────────────────────────────────
async function handleExport() {
  exportLoading.value = true
  try {
    await downloadScheduleExcel(currentMonth.value)
  } catch (e: any) {
    alert('Ошибка экспорта: ' + (e?.message ?? 'неизвестная ошибка'))
  } finally {
    exportLoading.value = false
  }
}

// ─── Day modal ────────────────────────────────────────────────────────────────
function openDayModal(route: DailyRoute) {
  selectedDayRoute.value = route
  // Pre-fill transport mode from rep's assigned car
  const repData = reps.value.find(r => r.id === route.rep_id)
  dayVehicleId.value = repData?.vehicle_id ?? null
  dayTransportMode.value = dayVehicleId.value ? 'car' : 'taxi'
  dayOptResult.value = null
  dayOptError.value = null
  selectedVariantId.value = null
  setDayRouteMessage(null)
  draftLocationIds.value = route.current_location_ids?.length
    ? [...route.current_location_ids]
    : route.visits.map((visit) => visit.location_id)
  draftRouteSource.value = route.route_source ?? 'generated'
  draftRouteLabel.value = route.route_label ?? null
  plannerPanel.value = 'draft'
  comparisonExpanded.value = false
  liveVisitStatuses.value = new Map()
  showDayModal.value = true
  void refreshDayRouteMetrics()
  void refreshDayProgress()
}

async function optimizeDayRoute() {
  if (!selectedDayRoute.value) return
  dayOptLoading.value = true
  dayOptError.value = null
  dayOptResult.value = null
  selectedVariantId.value = null
  plannerPanel.value = 'ai'
  try {
    const locationIds = currentLocationIds.value
    dayOptResult.value = await optimizeVariants(locationIds, selectedModel.value, {})
  } catch (e: any) {
    dayOptError.value = e?.message ?? 'Ошибка оптимизации'
  } finally {
    dayOptLoading.value = false
  }
}

function previewVariant(variant: RouteVariant) {
  selectedVariantId.value = variant.id
  draftLocationIds.value = [...variant.locations]
  draftRouteSource.value = 'ai'
  draftRouteLabel.value = variant.name
  comparisonExpanded.value = true
  setDayRouteMessage(`Предпросмотр: ${variant.name}. Проверьте разницу в метриках и при необходимости примените маршрут.`, 'info')
  void refreshDayRouteMetrics()
}

function resetDraftToCurrent() {
  draftLocationIds.value = [...currentLocationIds.value]
  draftRouteSource.value = selectedDayRoute.value?.route_source ?? 'generated'
  draftRouteLabel.value = selectedDayRoute.value?.route_label ?? null
  selectedVariantId.value = null
  setDayRouteMessage('Черновик снова совпадает с активным маршрутом.', 'info')
  void refreshDayRouteMetrics()
}

function moveDraftPoint(index: number, direction: -1 | 1) {
  const nextIndex = index + direction
  if (nextIndex < 0 || nextIndex >= draftLocationIds.value.length) return
  const nextOrder = [...draftLocationIds.value]
  ;[nextOrder[index], nextOrder[nextIndex]] = [nextOrder[nextIndex], nextOrder[index]]
  applyManualDraftOrder(nextOrder)
}

function applyManualDraftOrder(nextOrder: string[]) {
  draftLocationIds.value = nextOrder
  draftRouteSource.value = 'manual'
  draftRouteLabel.value = 'Ручной порядок'
  selectedVariantId.value = null
  comparisonExpanded.value = true
  setDayRouteMessage('Черновик маршрута изменён вручную. Сравните его с активным маршрутом перед применением.', 'info')
  void refreshDayRouteMetrics()
}

function onDraftDragStart(index: number, event: DragEvent) {
  draftDragFromIndex.value = index
  draftDragOverIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(index))
  }
}

function onDraftDragEnter(index: number) {
  if (draftDragFromIndex.value === null) return
  draftDragOverIndex.value = index
}

function onDraftDrop(index: number) {
  if (draftDragFromIndex.value === null) return
  const fromIndex = draftDragFromIndex.value
  draftDragFromIndex.value = null
  draftDragOverIndex.value = null
  if (fromIndex === index) return
  const nextOrder = [...draftLocationIds.value]
  const [movedLocation] = nextOrder.splice(fromIndex, 1)
  nextOrder.splice(index, 0, movedLocation)
  applyManualDraftOrder(nextOrder)
}

function onDraftDragEnd() {
  draftDragFromIndex.value = null
  draftDragOverIndex.value = null
}

async function applyDraftRoute() {
  if (!selectedDayRoute.value || !isDraftDirty.value) return
  confirmingVariant.value = true
  dayOptError.value = null
  try {
    if (draftRouteSource.value === 'ai' && selectedVariant.value && dayOptResult.value) {
      const payload: ConfirmVariantRequest = {
        name: `${selectedDayRoute.value.rep_name} — ${selectedDayRoute.value.date} (${selectedVariant.value.name})`,
        locations: selectedVariant.value.locations,
        total_distance_km: selectedVariant.value.metrics.distance_km,
        total_time_hours: selectedVariant.value.metrics.time_hours,
        total_cost_rub: selectedVariant.value.metrics.cost_rub,
        quality_score: selectedVariant.value.metrics.quality_score,
        model_used: dayOptResult.value.model_used,
        original_location_ids: originalLocationIds.value,
      }
      await confirmVariant(payload)
    }

    const updatedRoute = await saveDayRouteOverride({
      rep_id: selectedDayRoute.value.rep_id,
      date: selectedDayRoute.value.date,
      location_ids: draftLocationIds.value,
      original_location_ids: originalLocationIds.value,
      source: draftRouteSource.value === 'ai' ? 'ai' : 'manual',
      label: draftRouteLabel.value ?? undefined,
    })

    updateRouteInState(updatedRoute)
    draftLocationIds.value = [...(updatedRoute.current_location_ids ?? updatedRoute.visits.map((visit: VisitScheduleItem) => visit.location_id))]
    draftRouteSource.value = updatedRoute.route_source ?? 'generated'
    draftRouteLabel.value = updatedRoute.route_label ?? null
    plannerPanel.value = 'draft'
    comparisonExpanded.value = false
    setDayRouteMessage(
      `Маршрут применён: ${routeSourceLabel(updatedRoute.route_source)}${updatedRoute.route_label ? ` (${updatedRoute.route_label})` : ''}.`,
      'success'
    )
    await refreshDayRouteMetrics()
  } catch (e: any) {
    dayOptError.value = e?.message ?? 'Ошибка сохранения маршрута'
  } finally {
    confirmingVariant.value = false
  }
}

async function revertAppliedRoute() {
  if (!selectedDayRoute.value || !selectedDayRoute.value.has_route_override) return
  revertingDayRoute.value = true
  dayOptError.value = null
  try {
    const updatedRoute = await revertDayRouteOverride(
      selectedDayRoute.value.rep_id,
      selectedDayRoute.value.date,
    )
    updateRouteInState(updatedRoute)
    draftLocationIds.value = [...(updatedRoute.current_location_ids ?? updatedRoute.visits.map((visit: VisitScheduleItem) => visit.location_id))]
    draftRouteSource.value = updatedRoute.route_source ?? 'generated'
    draftRouteLabel.value = updatedRoute.route_label ?? null
    selectedVariantId.value = null
    comparisonExpanded.value = false
    setDayRouteMessage('Маршрут откатан к исходному порядку.', 'warning')
    await refreshDayRouteMetrics()
  } catch (e: any) {
    dayOptError.value = e?.message ?? 'Ошибка отката маршрута'
  } finally {
    revertingDayRoute.value = false
  }
}


function statusLabel(s: string): string {
  return ({ completed: '✓', skipped: '✗', planned: '·', cancelled: '—', rescheduled: '↺' } as Record<string, string>)[s] ?? s
}

function statusColor(s: string): string {
  return ({ completed: 'text-green-600', skipped: 'text-red-600', cancelled: 'text-gray-400', rescheduled: 'text-yellow-600', planned: 'text-gray-500' } as Record<string, string>)[s] ?? 'text-gray-500'
}

// ─── Category styling ─────────────────────────────────────────────────────────
function catDot(cat: string) {
  return `w-3 h-3 rounded-full ${catColor(cat)}`
}
function catBadge(cat: string | null) {
  return `${catColor(cat ?? '?')} text-white`
}
function catColor(cat: string) {
  return { A: 'bg-red-600', B: 'bg-orange-500', C: 'bg-yellow-500', D: 'bg-gray-500' }[cat] ?? 'bg-gray-600'
}
function visitChipClass(visit: VisitScheduleItem) {
  if (visit.status === 'completed') return 'bg-green-700 text-white'
  if (visit.status === 'skipped') return 'bg-red-900 text-red-300 line-through'
  if (visit.status === 'cancelled') return 'bg-gray-700 text-gray-500 line-through'
  return `${catColor(visit.location_category ?? '?')} text-white`
}

watch(showHolidays, async (val) => {
  if (val && allHolidays.value.length === 0) {
    allHolidaysLoading.value = true
    holidayToggleMsg.value = null
    allHolidays.value = await fetchHolidays({ year: parseInt(currentMonth.value.split('-')[0]) }).catch(() => [])
    allHolidaysLoading.value = false
  }
  if (!val) holidayToggleMsg.value = null
})

watch(
  [() => showDayModal.value, () => locationsById.value],
  ([isOpen]) => {
    if (isOpen && selectedDayRoute.value) {
      void refreshDayRouteMetrics()
    }
  },
  { deep: false }
)

async function loadLocations() {
  try {
    const list = await fetchAllLocations()
    const m = new Map<string, Location>()
    for (const loc of list) m.set(loc.id, loc)
    locationsById.value = m
  } catch (e) {
    console.warn('Failed to load locations for RouteMap', e)
  }
}

onMounted(() => {
  loadSchedule()
  loadReps()
  loadLocations()
  loadSkippedStash()
  fetchVehicles().then(v => { vehicles.value = v }).catch(() => {})
})
</script>

<style scoped>
.card { @apply bg-white rounded-lg border border-gray-200 shadow-sm; }
.input { @apply bg-white border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500; }
.label { @apply block text-xs text-gray-600 mb-1; }
.btn-primary { @apply bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded disabled:opacity-50; }
.btn-secondary { @apply bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 text-sm px-4 py-2 rounded; }
.btn-icon { @apply bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300 w-8 h-8 rounded flex items-center justify-center; }
.visit-chip { @apply text-xs px-2 py-0.5 rounded-full; }
.modal-overlay { @apply fixed inset-0 bg-black/50 flex items-center justify-center z-50; }
.modal { @apply bg-white border border-gray-200 rounded-lg p-6 w-full max-w-md shadow-xl; }
.planner-modal { @apply bg-white border border-gray-200 rounded-2xl p-6 w-full shadow-2xl; max-width: min(96vw, 1220px); max-height: calc(100vh - 2rem); overflow-y: auto; }
.planner-modal__header { @apply flex items-start justify-between gap-4 mb-4 pb-4 border-b border-gray-100; }
.planner-summary-card { @apply border border-gray-200 rounded-xl bg-gray-50 px-4 py-3; }
.planner-summary-card__label { @apply text-[11px] uppercase tracking-wide text-gray-500 mb-1; }
.planner-summary-card__value { @apply text-sm font-semibold text-gray-900; }
.planner-summary-card__hint { @apply text-xs text-gray-500 mt-1; }
.planner-tab { @apply rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-600 transition-colors; }
.planner-tab--active { @apply border-blue-600 bg-blue-600 text-white; }
.planner-route-row { @apply flex items-center gap-2 border border-gray-200 rounded-xl px-3 py-2 bg-white transition-colors; }
.map-link-btn { @apply inline-flex items-center gap-1 text-xs px-2 py-1 rounded border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 no-underline; }
.planner-route-row--drag { @apply border-blue-300 bg-blue-50; }
.planner-drag-handle { @apply text-gray-400 text-sm select-none cursor-grab; }
.planner-action-bar { @apply flex flex-wrap gap-2 mt-3 pt-3 border-t border-gray-100; }
.planner-empty-state { @apply rounded-xl border border-dashed border-gray-300 bg-gray-50 px-4 py-6 text-center text-sm text-gray-500; }
</style>
