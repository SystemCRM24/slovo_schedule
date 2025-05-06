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

/**
 * @param {Date} date
 * @returns {string} - строка даты в ISO формате
 * @example "2025-01-01"
 */
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
                for (const item of specialistScheduleItems.intervals) {
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
 * @param {{hours: number, minutes: number}} workingDayStart - данные о начале рабочего дня
 * @param {{hours: number, minutes: number}} workingDayEnd - данные о конце рабочего дня
 * @returns {Array<
 * {start: Date, end: Date, patient: {name: string, type: string} | null, status: "booked" | "confirmed" | "free" | "na"}
 * >}
 * список свободных и занятых промежутков
 */
export function getWorkingIntervalsFromSchedules(schedule, workSchedule, workingDayStart, workingDayEnd) {
    let intervals = [];
    const sortedWorkSchedule = workSchedule.sort(compareIntervalDates);
    const workingDayStartDt = new Date(sortedWorkSchedule[0].start);
    workingDayStartDt.setHours(workingDayStart.hours, workingDayStart.minutes);
    const workingDayEndDt = new Date(sortedWorkSchedule[0].start);
    workingDayEndDt.setHours(workingDayEnd.hours, workingDayEnd.minutes);
    // если задан график работы и рабочий день не начинается в наиболее раннее возможное время, то добавляем
    // недоступный промежуток с наиболее раннего времени по начало рабочего дня
    // аналогично с концом рабочего дня
    if (sortedWorkSchedule.length > 0) {
        if (workingDayStartDt.getTime() !== sortedWorkSchedule[0].start.getTime()) {
            intervals.push({
                start: workingDayStartDt,
                end: sortedWorkSchedule[0].start,
                patient: null,
                status: "na",
            });
        }
        if (workingDayEndDt.getTime() !== sortedWorkSchedule[sortedWorkSchedule.length - 1].end.getTime()) {
            intervals.push({
                start: sortedWorkSchedule[sortedWorkSchedule.length - 1].end,
                end: workingDayEndDt,
                patient: null,
                status: "na"
            });
        }
    }
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
        // находим все занятия внутри рабочего промежутка
        const scheduleIntervalsInRange = findScheduleIntervalsInRange(schedule, startTimestamp, endTimestamp);
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

/**
 * Функция поиска занятий в промежутке рабочего графика
 * @param {Array<
 * {start: Date, end: Date, patient: {name: string, type: string} | null, status: "booked" | "confirmed" | "free" | "na"}
 * >} schedule
 * расписание занятий по специалисту
 * @param {number} startTimestamp - начало промежутка
 * @param {number} endTimestamp - конец промежутка
 * @returns {Array} - занятия внутри промежутка
 */
export function findScheduleIntervalsInRange(schedule, startTimestamp, endTimestamp) {
    return schedule.filter(
        item => startTimestamp <= item.start.getTime() && item.end.getTime() <= endTimestamp
    ).sort(compareIntervalDates);
}

/**
 *
 * @param {
 * {start: Date, end: Date}
 * } interval1
 * @param {
 * {start: Date, end: Date}
 * } interval2
 * @returns {Boolean} - пересекаются ли временные промежутки
 */
export function areIntervalsOverlapping(interval1, interval2) {
    const startD = interval1.start.getTime(); // 09:30
    const startDate = interval2.start.getTime(); // 10:00
    const endD = interval1.end.getTime(); // 10:00
    const endDate = interval2.end.getTime(); // 10:15
    return (startD >= startDate && startD < endDate) ||
        (startDate >= startD && startDate < endD);
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
    const startTime = getTimeStringFromDate(d1);
    const endTime = getTimeStringFromDate(d2)
    return [startTime, endTime].join(' - ');
}

/**
 *
 * @param d {Date | null | undefined}
 * @returns {string | undefined} строковое представление времени без секунд в 24-часовом формате
 * @example "12:00"
 */
export function getTimeStringFromDate(d) {
    return d ? d.toLocaleTimeString().split(':').slice(0, -1).join(':') : undefined;
}

/**
 *
 * @param {Date} date - дата без времени
 * @param {number} hours - часы
 * @param {number} minutes - минуты
 * @returns {Date} объект даты с указанными часом и минутами
 */
export function getDateWithTime(date, hours, minutes) {
    const newDate = new Date(date);
    newDate.setHours(hours, minutes);
    return newDate;
}

/**
 *
 * @param {{start: Date | undefined, end: Date | undefined}} interval
 * @returns {boolean}
 */
export function isIntervalValid(interval) {
    return interval.start !== undefined && interval.end !== undefined && (interval.start < interval.end);
}

/**
 * @param {
 * {start: Date | undefined, end: Date | undefined, patientName: string | undefined, patientType: string | undefined}
 * } schedule - проверяемый объект занятия в расписании
 * @param {
 * Array<{start: Date | undefined, end: Date | undefined, patientName: string | undefined, patientType: string | undefined}>
 *     } newSchedules - список всех новых занятий
 * @param {Array<
 * {start: Date, end: Date, patient: {name: string, type: string} | null, status: "booked" | "confirmed" | "free" | "na"}
 * >} daySchedule - текущее расписание занятий на день
 * @param {{start: Date, end: Date} | Array<{start: Date, end: Date}>} workSchedule - текущее промежуток графика работы на день
 * @returns {Boolean} валидный ли интервал
 */
export function isNewScheduleIntervalValid(schedule, newSchedules, daySchedule, workSchedule) {
    if (schedule.start !== undefined && schedule.end !== undefined) {
        let inWorkTime;
        // если нам пришел массив, то нужно проверить все промежутки
        if (Array.isArray(workSchedule)) {
            const intersections = workSchedule.map(
                sched => {
                    return schedule.start.getTime() >= sched.start.getTime() &&
                        schedule.end.getTime() <= sched.end.getTime()
                }
            );
            inWorkTime = intersections.some(item => item === true);
        } else {
            inWorkTime = schedule.start.getTime() >= workSchedule.start.getTime() &&
                schedule.end.getTime() <= workSchedule.end.getTime()
        }
        if (!inWorkTime) {
            console.log(schedule, 'not in work time')
            return false;
        }
        const schedules = [newSchedules.filter(interval => isIntervalValid(interval)), daySchedule];
        for (const scheduleArr of schedules) {
            const intervalsInRange = findScheduleIntervalsInRange(
                scheduleArr, schedule.start.getTime(), schedule.end.getTime()
            );
            if (intervalsInRange.length > 0) {
                console.log(schedule, 'intersects one of', scheduleArr);
                return false;
            }
            for (const interval of scheduleArr) {
                if (areIntervalsOverlapping(schedule, interval)) {
                    console.log(schedule, 'overlapping', interval);
                    return false;
                }
            }
        }
        console.info('everything ok with', schedule);
        return true;
    }
}


/**
 * @param {
 * {start: Date | undefined, end: Date | undefined, patientId: string | undefined | Number, patientType: string | undefined}
 * } schedule - проверяемый объект занятия в расписании
 * @param {
 * Array<{start: Date | undefined, end: Date | undefined, patientName: string | undefined, patientType: string | undefined}>
 *     } newSchedules - список всех новых занятий
 * @param {Array<
 * {start: Date, end: Date, patient: {name: string, type: string} | null, status: "booked" | "confirmed" | "free" | "na"}
 * >} daySchedule - текущее расписание занятий на день
 * @param {{start: Date, end: Date}} workSchedule - текущее промежуток графика работы на день
 * @returns {Boolean} является ли новое занятие валидным
 */
export function isNewScheduleValid(schedule, newSchedules, daySchedule, workSchedule) {
    const invalidPatientValues = ['', null, undefined];
    return isNewScheduleIntervalValid(schedule, newSchedules, daySchedule, workSchedule) && !(
        invalidPatientValues.includes(schedule.patientId) || invalidPatientValues.includes(schedule.patientType)
    );
}

/**
 * @param {
 * {start: Date | undefined, end: Date | undefined}
 * } newWorkSchedule - проверяемый объект занятия в расписании
 * @param {
 * Array<{start: Date | undefined, end: Date | undefined, patientName: string | undefined, patientType: string | undefined}>
 *     } newSchedules - список всех новых занятий
 * @param {Array<
 * {start: Date, end: Date, patient: {name: string, type: string} | null, status: "booked" | "confirmed" | "free" | "na"}
 * >} daySchedule - текущее расписание занятий на день
 * @param {{start: Date, end: Date}} dayWorkSchedule - текущее промежуток графика работы на день
 * @returns {Boolean} является ли новый рабочий график валидным
 */
export function isNewWorkScheduleValid(newWorkSchedule, newSchedules,
                                       daySchedule, dayWorkSchedule) {
    // базовая проверка интервала на валидность
    if (!isIntervalValid(newWorkSchedule)) {
        return false;
    }
    // проверяем, не пересекается ли с другими рабочими промежутками и занятиями
    const potentiallyOverlappingSchedules = [...newSchedules.filter(isIntervalValid), ...daySchedule, ...dayWorkSchedule];
    for (const potentiallyOverlappingSchedule of potentiallyOverlappingSchedules) {
        if (
            areIntervalsOverlapping(newWorkSchedule, potentiallyOverlappingSchedule) &&
            !(
                potentiallyOverlappingSchedule.start >= newWorkSchedule.start &&
                    potentiallyOverlappingSchedule.end <= newWorkSchedule.end
            )
        ) {
            console.log(newWorkSchedule, 'overlapping', potentiallyOverlappingSchedule)
            return false;
        }
    }
    return true;
}
