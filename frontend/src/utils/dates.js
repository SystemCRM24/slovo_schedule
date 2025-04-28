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


/**
 * @param {Array<
 * {start: Date, end: Date, patient: {name: string, type: string} | null, status: "booked" | "confirmed" | "free" | "na"}
 * >} schedule
 * расписание занятий по специалисту
 * @param {Array<{start: Date, end: Date}>} workSchedule
 * рабочий график специалиста на конкретную дату
 * @returns {Array<
 * {start: Date, end: Date, patient: {name: string, type: string} | null, status: "booked" | "confirmed" | "free" | "na"}
 * >}
 * список свободных и занятых промежутков
 */
export function getWorkingIntervalsFromSchedules(schedule, workSchedule) {
    let intervals = [];
    const sortedWorkSchedule = workSchedule.sort(compareIntervalDates);
    for (const [index, workingInterval] of Object.entries(sortedWorkSchedule)) {
        // добавляем нерабочий интервал между рабочими промежутками
        if (index > 0) {
            intervals.push({
                start: sortedWorkSchedule[index - 1].end,
                end: workingInterval.start,
                patient: null,
                status: "na"
            });
        }
        const [startTimestamp, endTimestamp] = [
            workingInterval.start.getTime(), workingInterval.end.getTime()
        ];
        // находим все интервалы внутри рабочего промежутка
        const scheduleIntervalsInRange = schedule.filter(
            item => startTimestamp <= item.start.getTime() && item.end.getTime() <= endTimestamp
        ).sort(compareIntervalDates);
        let currentStartDt = new Date(startTimestamp);
        // формируем интервалы внутри рабочего промежутка
        for (const interval of scheduleIntervalsInRange) {
            if (interval.start.getTime() === currentStartDt.getTime()) {
                intervals.push(interval);
                currentStartDt = interval.end;
            } else {
                const newIntervals = [
                    {
                        start: currentStartDt,
                        end: interval.start,
                        patient: null,
                        status: "free"
                    },
                    interval
                ];
                intervals = [...intervals, ...newIntervals];
                currentStartDt = interval.end;
            }
        }
        // если окончание последнего занятия не совпало с окончанием рабочего промежутка, то добавляем последний интервал
        if (currentStartDt < workingInterval.end) {
            intervals.push({
                start: currentStartDt,
                end: workingInterval.end,
                patient: null,
                status: "free",
            });
        }
    }
    return intervals.sort(compareIntervalDates);
}

function compareIntervalDates(a, b) {
    return a.start - b.start;
}

/**
 *
 * @param {Date} d1
 * @param {Date} d2
 * @returns {string} строковое представление временного промежутка
 * @example "09:00 - 09:30"
 */
export function getIntervalTimeString(d1, d2) {
    const startTime = d1.toLocaleTimeString().split(':').slice(0, -1).join(':');
    const endTime = d2.toLocaleTimeString().split(':').slice(0, -1).join(':')
    return [startTime, endTime].join(' - ');
}
