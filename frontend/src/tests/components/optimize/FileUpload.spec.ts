import { mount } from '@vue/test-utils'
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import FileUpload from '@/components/optimize/FileUpload.vue'
import { nextTick } from 'vue'

describe('FileUpload.vue', () => {
  let wrapper: any
  let mockFileReaderInstance: any
  let mockFileReaderConstructor: any
  
  beforeEach(() => {
    // Создаем mock для FileReader
    mockFileReaderInstance = {
      readAsText: vi.fn(),
      result: '',
      onload: null as any,
      onerror: null as any,
      onabort: null as any,
      onloadend: null as any,
      onloadstart: null as any,
      onprogress: null as any,
      readyState: 0,
      error: null,
      abort: vi.fn(),
      DONE: 2,
      EMPTY: 0,
      LOADING: 1
    }
    
    mockFileReaderConstructor = vi.fn(() => mockFileReaderInstance)
    global.FileReader = mockFileReaderConstructor as any
    
    wrapper = mount(FileUpload)
  })
  
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders file upload component with drag & drop area', () => {
    expect(wrapper.find('h3').text()).toBe('Загрузка магазинов из файла')
    expect(wrapper.find('p.text-gray-600').text()).toContain('CSV или JSON')
    
    // Проверяем drag & drop зону
    const dropZone = wrapper.find('div.border-dashed')
    expect(dropZone.exists()).toBe(true)
    expect(dropZone.text()).toContain('Нажмите для выбора файла')
    expect(dropZone.text()).toContain('Поддерживаемые форматы: CSV, JSON')
    
    // Проверяем скрытый input
    expect(wrapper.find('input[type="file"]').exists()).toBe(true)
    expect(wrapper.find('input[type="file"]').attributes('accept')).toBe('.csv,.json,.txt,text/csv,application/json')
  })

  it('opens file dialog when drop zone is clicked', async () => {
    const fileInput = wrapper.find('input[type="file"]')
    const clickSpy = vi.spyOn(fileInput.element, 'click')
    
    const dropZone = wrapper.find('div.border-dashed')
    await dropZone.trigger('click')
    
    expect(clickSpy).toHaveBeenCalled()
  })

  it('handles drag over event', async () => {
    const dropZone = wrapper.find('div.border-dashed')
    
    await dropZone.trigger('dragover')
    await nextTick()
    
    expect(wrapper.vm.isDragging).toBe(true)
    expect(dropZone.classes()).toContain('border-blue-500')
    expect(dropZone.classes()).toContain('bg-blue-50')
  })

  it('handles drag leave event', async () => {
    const dropZone = wrapper.find('div.border-dashed')
    
    await dropZone.trigger('dragover')
    await nextTick()
    expect(wrapper.vm.isDragging).toBe(true)
    
    await dropZone.trigger('dragleave')
    await nextTick()
    expect(wrapper.vm.isDragging).toBe(false)
  })

  it('handles file drop event', async () => {
    const dropZone = wrapper.find('div.border-dashed')
    
    const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
    const dataTransfer = {
      files: [mockFile]
    }
    
    await dropZone.trigger('drop', { dataTransfer })
    
    expect(wrapper.vm.isDragging).toBe(false)
    expect(mockFileReaderConstructor).toHaveBeenCalled()
  })

  it('validates file size (max 5MB)', async () => {
    const mockLargeFile = new File(['x'.repeat(6 * 1024 * 1024)], 'large.csv', { type: 'text/csv' })
    
    await wrapper.vm.processFile(mockLargeFile)
    await nextTick()
    
    expect(wrapper.vm.error).toBe('Файл слишком большой. Максимальный размер: 5MB')
  })

  it('validates file format', async () => {
    const mockInvalidFile = new File(['test'], 'test.txt', { type: 'text/plain' })
    
    await wrapper.vm.processFile(mockInvalidFile)
    await nextTick()
    
    expect(wrapper.vm.error).toBe('Неподдерживаемый формат файла. Используйте CSV или JSON.')
  })

  it('parses CSV files correctly', async () => {
    const csvContent = `name,city,street,houseNumber,latitude,longitude
Магазин 1,Москва,Тверская,15,55.7558,37.6173
Магазин 2,Санкт-Петербург,Невский проспект,20,59.9343,30.3351`
    
    // Устанавливаем результат для FileReader
    mockFileReaderInstance.result = csvContent
    
    const mockFile = new File([csvContent], 'test.csv', { type: 'text/csv' })
    
    // Запускаем парсинг
    await wrapper.vm.parseCSV(mockFile)
    
    // Симулируем onload событие
    if (mockFileReaderInstance.onload) {
      mockFileReaderInstance.onload({ target: { result: csvContent } })
    }
    
    await nextTick()
    
    // Проверяем заголовки
    expect(wrapper.vm.previewHeaders).toEqual(['name', 'city', 'street', 'houseNumber', 'latitude', 'longitude'])
    
    // Проверяем данные предпросмотра (только первые 2 строки)
    expect(wrapper.vm.previewData).toHaveLength(2)
    expect(wrapper.vm.previewData[0]).toEqual({
      name: 'Магазин 1',
      city: 'Москва',
      street: 'Тверская',
      houseNumber: '15',
      latitude: '55.7558',
      longitude: '37.6173'
    })
  })

  it('parses JSON files correctly', async () => {
    const jsonContent = JSON.stringify([
      {
        name: 'Магазин 1',
        city: 'Москва',
        street: 'Тверская',
        houseNumber: '15',
        latitude: 55.7558,
        longitude: 37.6173
      },
      {
        name: 'Магазин 2',
        city: 'Санкт-Петербург',
        street: 'Невский проспект',
        houseNumber: '20',
        latitude: 59.9343,
        longitude: 30.3351
      }
    ])
    
    // Устанавливаем результат для FileReader
    mockFileReaderInstance.result = jsonContent
    
    const mockFile = new File([jsonContent], 'test.json', { type: 'application/json' })
    
    // Запускаем парсинг
    await wrapper.vm.parseJSON(mockFile)
    
    // Симулируем onload событие
    if (mockFileReaderInstance.onload) {
      mockFileReaderInstance.onload({ target: { result: jsonContent } })
    }
    
    await nextTick()
    
    // Проверяем заголовки
    expect(wrapper.vm.previewHeaders).toEqual(['name', 'city', 'street', 'houseNumber', 'latitude', 'longitude'])
    
    // Проверяем данные предпросмотра
    expect(wrapper.vm.previewData).toHaveLength(2)
    expect(wrapper.vm.previewData[0]).toEqual({
      name: 'Магазин 1',
      city: 'Москва',
      street: 'Тверская',
      houseNumber: '15',
      latitude: 55.7558,
      longitude: 37.6173
    })
  })

  it('handles file reader errors', async () => {
    const mockFile = new File(['test'], 'test.csv', { type: 'text/csv' })
    
    // Запускаем парсинг
    await wrapper.vm.parseCSV(mockFile)
    
    // Симулируем onerror событие
    if (mockFileReaderInstance.onerror) {
      mockFileReaderInstance.onerror(new Error('Read error'))
    }
    
    await nextTick()
    
    expect(wrapper.vm.error).toBe('Ошибка при чтении файла')
  })

  it('validates required fields in uploaded data', () => {
    const invalidData = [
      {
        name: '', // Пустое имя
        city: 'Москва',
        street: 'Тверская',
        houseNumber: '15',
        latitude: '55.7558',
        longitude: '37.6173'
      }
    ]
    
    wrapper.vm.validateData(invalidData)
    
    expect(wrapper.vm.validationErrors).toContain('Строка 2: Отсутствует обязательное поле "name"')
  })

  it('validates latitude and longitude ranges', () => {
    const invalidData = [
      {
        name: 'Магазин 1',
        city: 'Москва',
        street: 'Тверская',
        houseNumber: '15',
        latitude: '100', // Некорректная широта
        longitude: '200' // Некорректная долгота
      }
    ]
    
    wrapper.vm.validateData(invalidData)
    
    expect(wrapper.vm.validationErrors).toContain('Строка 2: Некорректная широта "100"')
    expect(wrapper.vm.validationErrors).toContain('Строка 2: Некорректная долгота "200"')
  })

  it('validates house number format', () => {
    const invalidData = [
      {
        name: 'Магазин 1',
        city: 'Москва',
        street: 'Тверская',
        houseNumber: 'abc', // Некорректный номер
        latitude: '55.7558',
        longitude: '37.6173'
      }
    ]
    
    wrapper.vm.validateData(invalidData)
    
    expect(wrapper.vm.validationErrors).toContain('Строка 2: Некорректный номер дома "abc"')
  })

  it('generates locations from parsed data', () => {
    const testData = [
      {
        name: 'Магазин 1',
        city: 'москва', // с маленькой буквы
        street: 'Тверская',
        houseNumber: '15',
        latitude: '55.7558',
        longitude: '37.6173',
        timeWindowStart: '09:00',
        timeWindowEnd: '18:00',
        priority: 'high'
      }
    ]
    
    wrapper.vm.allFileData = testData
    const locations = wrapper.vm.generateMockLocationsFromFile()
    
    expect(locations).toHaveLength(1)
    expect(locations[0]).toMatchObject({
      name: 'Магазин 1',
      city: 'Москва', // Должно быть с заглавной
      street: 'Тверская',
      houseNumber: '15',
      latitude: 55.7558,
      longitude: 37.6173,
      timeWindowStart: '09:00',
      timeWindowEnd: '18:00',
      priority: 'high'
    })
  })

  it('emits add-locations event when location is added to form', async () => {
    const mockLocation = {
      id: 'test-1',
      name: 'Тестовый магазин',
      city: 'Москва',
      street: 'Тверская',
      houseNumber: '15',
      latitude: 55.7558,
      longitude: 37.6173,
      timeWindowStart: '09:00',
      timeWindowEnd: '18:00',
      priority: 'medium' as const
    }
    
    wrapper.vm.addLocationToForm(mockLocation)
    await nextTick()
    
    expect(wrapper.emitted('add-locations')).toBeTruthy()
    if (wrapper.emitted('add-locations')) {
      expect(wrapper.emitted('add-locations')![0][0]).toEqual([mockLocation])
    }
    
    // Проверяем сообщение об успехе
    expect(wrapper.vm.successMessage).toBe(`Магазин "${mockLocation.name}" добавлен в форму`)
  })

  it('shows upload button only when valid data is present', async () => {
    // Изначально кнопка не должна отображаться
    expect(wrapper.find('button.bg-blue-600').exists()).toBe(false)
    
    // Добавляем валидные данные
    wrapper.vm.previewData = [{ name: 'Магазин 1', city: 'Москва' }]
    wrapper.vm.validationErrors = []
    await nextTick()
    
    expect(wrapper.find('button.bg-blue-600').exists()).toBe(true)
  })

  
  it('shows success message after successful upload', async () => {
    wrapper.vm.successMessage = 'Успешно загружено 5 магазинов'
    await nextTick()
    
    const successDiv = wrapper.find('div.bg-green-50')
    expect(successDiv.exists()).toBe(true)
    expect(successDiv.text()).toContain('Успешно загружено 5 магазинов')
  })

  it('shows uploaded locations list', async () => {
    wrapper.vm.uploadedLocations = [
      {
        id: 'loc-1',
        name: 'Магазин 1',
        city: 'Москва',
        street: 'Тверская',
        houseNumber: '15',
        latitude: 55.7558,
        longitude: 37.6173,
        timeWindowStart: '09:00',
        timeWindowEnd: '18:00',
        priority: 'medium' as const
      }
    ]
    
    await nextTick()
    
    expect(wrapper.text()).toContain('Загруженные магазины')
    expect(wrapper.text()).toContain('Магазин 1')
    expect(wrapper.text()).toContain('Москва, Тверская, д. 15')
  })

  it('clears uploaded data when clear button is clicked', async () => {
    wrapper.vm.uploadedLocations = [{ 
      id: 'loc-1', 
      name: 'Магазин 1',
      city: 'Москва',
      street: 'Тверская',
      houseNumber: '15'
    }]
    await nextTick()
    
    const clearButton = wrapper.find('button.bg-white')
    await clearButton.trigger('click')
    
    expect(wrapper.vm.uploadedLocations).toHaveLength(0)
    expect(wrapper.vm.successMessage).toBe('Загруженные данные очищены')
  })

  it('handles CSV files with empty lines', async () => {
    const csvContent = `name,city,street,houseNumber,latitude,longitude
Магазин 1,Москва,Тверская,15,55.7558,37.6173

Магазин 2,Санкт-Петербург,Невский проспект,20,59.9343,30.3351
`
    
    mockFileReaderInstance.result = csvContent
    
    const mockFile = new File([csvContent], 'test.csv', { type: 'text/csv' })
    
    await wrapper.vm.parseCSV(mockFile)
    
    if (mockFileReaderInstance.onload) {
      mockFileReaderInstance.onload({ target: { result: csvContent } })
    }
    
    await nextTick()
    
    // Должны быть только 2 строки данных (пустая строка игнорируется)
    expect(wrapper.vm.previewData).toHaveLength(2)
  })

  it('handles JSON files that are not arrays', async () => {
    const invalidJsonContent = JSON.stringify({
      name: 'Магазин 1',
      city: 'Москва'
    })
    
    mockFileReaderInstance.result = invalidJsonContent
    
    const mockFile = new File([invalidJsonContent], 'test.json', { type: 'application/json' })
    
    await wrapper.vm.parseJSON(mockFile)
    
    if (mockFileReaderInstance.onload) {
      mockFileReaderInstance.onload({ target: { result: invalidJsonContent } })
    }
    
    await nextTick()
    
    expect(wrapper.vm.error).toBe('JSON должен содержать массив объектов')
  })

  
  it('can trigger file input programmatically', () => {
    expect(typeof wrapper.vm.triggerFileInput).toBe('function')
    
    const fileInput = wrapper.find('input[type="file"]')
    const clickSpy = vi.spyOn(fileInput.element, 'click')
    
    wrapper.vm.triggerFileInput()
    
    expect(clickSpy).toHaveBeenCalled()
  })
})