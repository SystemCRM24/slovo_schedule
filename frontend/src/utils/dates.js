/**
 * @param {Date} fromDate - дата начала промежутка
 * @param {Date} toDate - дата конца промежутка
 * @returns {Array<Date>} - промежуток дат, включая дату начала и конца
 */
export function getDateRange(fromDate, toDate) {
    let range = [];
    for (let currentDate = new Date(fromDate); currentDate <= toDate; currentDate.setDate(currentDate.getDate() + 1)) {
        range.push(new Date(currentDate))
    }
    return range
}

export function getISODate(date) {
    return date && date.toISOString().split('T')[0];
}

/**
 @param {Object<string, Object<Date, Array<{'start': Date, 'end': Date}>>>} schedule - расписание по специалистам
 @returns {{'start': {'hours': Number, 'minutes': Number}, 'end': {'hours': Number, 'minutes': Number}}}
 - начало и конец рабочего дня
 */
export function getWorkingDayFromSchedule(schedule) {
    let start = {hours: 23, minutes: 59};
    let end = {hours: 0, minutes: 0};
    if (Object.keys(schedule).length > 0) {
        for (const specialistSchedule of Object.values(schedule)) {
            for (const specialistScheduleItems of Object.values(specialistSchedule)) {
                for (const item of specialistScheduleItems) {
                    const startHours = item.start.getHours()
                    const startMinutes = item.start.getMinutes();
                    const endHours = item.end.getHours();
                    const endMinutes = item.end.getMinutes();
                    if (startHours < start.hours || (startHours === start.hours && startMinutes < start.minutes)) {
                        start = {hours: startHours, minutes: startMinutes};
                    }
                    if (endHours > end.hours || (endHours === end.hours && endMinutes > end.minutes)) {
                        end = {hours: endHours, minutes: endMinutes};
                    }
                }
            }
        }
    }
    return {start: start, end: end}
}

/**
 *
 * @param {Date} dt1
 * @param {Date} dt2
 * @returns {number} - разница между датами в минутах
 */
export function getDatesDiffInMinutes(dt1, dt2) {
    return Math.floor(Math.abs((dt2 - dt1) / 1000 / 60));
}
