/**
 * @param {Date} fromDate - дата начала промежутка
 * @param {Date} toDate - дата конца промежутка
 * @returns {Array<Date>} - промежуток дат, включая дату начала и конца
 */
export function getDateRange(fromDate, toDate) {
    let range = [];
    for (let currentDate = new Date(fromDate); currentDate <= toDate; currentDate.setDate(currentDate.getDate() + 1)) {
        range.push(new Date(currentDate))
        console.log(range);
    }
    return range
}

export function getISODate(date) {
    return date && date.toISOString().split('T')[0];
}
