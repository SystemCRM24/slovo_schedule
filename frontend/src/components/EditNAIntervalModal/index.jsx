import React, { useCallback, useMemo, useState } from 'react';
import CustomModal from "../ui/Modal/index.jsx";
import {
    areIntervalsOverlapping,
    getDateWithTime,
    getTimeStringFromDate,
    isIntervalValid,
} from "../../utils/dates.js";
import useSchedules from "../../hooks/useSchedules.js";
import { useDayContext } from "../../contexts/Day/provider.jsx";
import useSpecialist from "../../hooks/useSpecialist.js";
import apiClient from "../../api/index.js";
import { Button, FormControl, InputGroup, Form } from "react-bootstrap";
import Holidays from 'date-holidays';

const EditNAInterval = ({ show, setShow, startDt, endDt }) => {
    const [workIntervals, setWorkIntervals] = useState([]);
    const [loading, setLoading] = useState(false);
    const {
        generalWorkSchedule,
        setGeneralWorkSchedule,
        workSchedule
    } = useSchedules();
    const date = useDayContext();
    const { specialistId, specialist } = useSpecialist();
    const dayOfWeek = date.toLocaleString('ru-RU', { weekday: 'long' });
    const dateString = date.toLocaleDateString();
    const [checkbox, setCheckbox] = useState(false)
    const holidays = new Holidays('RU');

    const maxStartTime = useMemo(() => {
        const maxDt = new Date(endDt);
        maxDt.setMinutes(endDt.getMinutes() - 1);
        return maxDt;
    }, [endDt])

    const onTimeInputChange = async (idx, attrName, value) => {
        const newIntervals = workIntervals.map((interval, index) => {
            if (index === idx) {
                const [hoursString, minutesString] = value.split(':');
                const hours = parseInt(hoursString);
                const minutes = parseInt(minutesString);
                return { ...interval, [attrName]: getDateWithTime(date, hours, minutes) };
            } else {
                return interval;
            }
        });
        setWorkIntervals(newIntervals);
    }

    const isHoliday = (date) => {
        const holidaysList = holidays.getHolidays(date.getFullYear());
        return holidaysList.some(holiday => {
            const holidayDate = new Date(holiday.date);
            return holidayDate.toISOString().split('T')[0] === date.toISOString().split('T')[0];
        });
    };

    const onAddButtonClick = () => {
        setWorkIntervals([...workIntervals, { start: undefined, end: undefined }])
    }

    const onRemoveButtonClick = async (idx) => {
        setWorkIntervals(workIntervals.filter((value, index) => index !== idx));
    }

    const handleCheckboxChange = (e) => {
        setCheckbox(e.target.checked);
    };

    function mergeIntervals(intervals) {
        if (!intervals.length) return [];

        const sorted = [...intervals].sort((a, b) => a.start.getTime() - b.start.getTime());

        const merged = [sorted[0]];

        for (const current of sorted.slice(1)) {
            const last = merged[merged.length - 1];

            if (current.start.getTime() <= last.end.getTime()) {
                merged[merged.length - 1] = {
                    start: last.start,
                    end: current.end.getTime() > last.end.getTime() ? current.end : last.end,
                };
            } else {
                merged.push(current);
            }
        }

        return merged;
    }

    const handleSubmit = async () => {
        setLoading(true);
        const newWorkIntervals = [...workSchedule.intervals, ...workIntervals];
        const newSchedules = [];

        if (checkbox) {
            let currentDate = new Date(date);
            const endDate = new Date(date);
            endDate.setDate(endDate.getDate() + 365);
            const response = await apiClient.getWorkSchedules(currentDate, endDate);
            const id = response[specialistId][currentDate].id
            const schedulesForSpecialist = response[specialistId] || [];

            for (let i = 0; i <= 48; i++) {
                if (isHoliday(currentDate)) {
                    currentDate.setDate(currentDate.getDate() + 7);
                    continue;
                }
                const adjustedIntervals = workIntervals.map(interval => ({
                    start: new Date(
                        currentDate.getFullYear(),
                        currentDate.getMonth(),
                        currentDate.getDate(),
                        interval.start.getHours(),
                        interval.start.getMinutes()
                    ),
                    end: new Date(
                        currentDate.getFullYear(),
                        currentDate.getMonth(),
                        currentDate.getDate(),
                        interval.end.getHours(),
                        interval.end.getMinutes()
                    )
                }))

                const normalizedCurrentDate = currentDate.toString();
                const existingSchedule = schedulesForSpecialist[normalizedCurrentDate];
                console.log("existingSchedule", existingSchedule)
                console.log("workSchedule", workSchedule)
                let intervalsToSave = adjustedIntervals;

                if (existingSchedule) {
                    intervalsToSave = [...existingSchedule.intervals, ...adjustedIntervals];
                }
                intervalsToSave = mergeIntervals(intervalsToSave);

                try {
                    let result
                    if (existingSchedule) {
                        result = await apiClient.updateWorkScheduleMassive(existingSchedule.id, {
                            specialist: specialistId,
                            date: currentDate,
                            intervals: intervalsToSave,
                        })
                    } else {
                        continue
                    }
                    if (result) {
                        console.log("result", result)
                        newSchedules.push({
                            date: new Date(currentDate),
                            data: { id: existingSchedule.id, intervals: intervalsToSave },
                        });
                    }
                } catch (error) {
                    console.error(`Ошибка для даты ${currentDate}:`, error);
                }
                currentDate.setDate(currentDate.getDate() + 7);
            }
        } else {
            try {
                const response = await apiClient.getWorkSchedules(date, date);
                const id = response[specialistId][date].id
                const result = await apiClient.updateWorkSchedule(id.toString(), {
                    specialist: specialistId,
                    date: date,
                    intervals: newWorkIntervals,
                });
                console.log("result", result)
                console.log("workSchedule", workSchedule)
                if (result) {
                    newSchedules.push({
                        date: new Date(date),
                        data: { id: id, intervals: newWorkIntervals },
                    });
                    console.log("newSchedules", newSchedules)
                }
            } catch (error) {
                console.error(`Ошибка для даты ${date}:`, error);
            }
        }

        setGeneralWorkSchedule(prevSchedule => {
            const newState = {
                ...prevSchedule,
                [specialistId]: {
                    ...(prevSchedule[specialistId] || {}),
                    ...newSchedules.reduce((acc, { date, data }) => {
                        acc[date] = data;
                        return acc;
                    }, {}),
                },
            };
            console.log('Updated generalWorkSchedule:', newState);
            return newState;
        });

        setLoading(false);
        setShow(false);
    };

    const isNewIntervalValid = useCallback((interval, index) => {
        if (interval.start !== undefined && interval.end !== undefined) {
            if (interval.start.getTime() < startDt.getTime() || interval.end.getTime() > endDt.getTime()) {
                return false;
            }
            const intervalsWithoutCurrent = workIntervals.filter((value, idx) => idx !== index);
            for (const interv of intervalsWithoutCurrent) {
                if (isIntervalValid(interv) && areIntervalsOverlapping(interval, interv)) {
                    console.log(interval, 'overlapping', interv);
                    return false;
                }
            }
            return true;
        } else {
            return false;
        }
    }, [endDt, startDt, workIntervals]);

    const areIntervalsValid = useMemo(() => {
        return workIntervals.map(isNewIntervalValid).every(elem => elem === true)
    }, [isNewIntervalValid, workIntervals]);

    const areNewSchedulesValid = useMemo(() => {
        return workIntervals.map(isNewIntervalValid).every(elem => elem === true);
    }, [isNewIntervalValid, workIntervals])

    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={`${specialist.name} - ${dayOfWeek} ${dateString} ${getTimeStringFromDate(startDt)}
             - ${getTimeStringFromDate(endDt)}`}
            primaryBtnDisabled={workIntervals.length < 1 || loading || !areIntervalsValid || !areNewSchedulesValid}
            primaryBtnText={'Сохранить'}
            handlePrimaryBtnClick={handleSubmit}
        >
            <div className="d-flex flex-column justify-content-center gap-2">
                {workIntervals.map((interval, idx) => {
                    return (
                        <div
                            className={'d-flex justify-content-between align-items-center gap-3'}
                            key={`${date}_new_interval_block_${idx}`}
                        >
                            <InputGroup style={{ width: "50%" }}>
                                <FormControl
                                    type={'time'}
                                    key={`${date}_new_interval_${idx}_start`}
                                    value={getTimeStringFromDate(interval.start)}
                                    name={'start'}
                                    min={getTimeStringFromDate(startDt)}
                                    max={getTimeStringFromDate(maxStartTime)}
                                    onChange={async (e) => {
                                        await onTimeInputChange(idx, e.target.name, e.target.value)
                                    }}
                                    style={{ textAlign: "center" }}
                                    required
                                    isInvalid={!interval.start}
                                />
                            </InputGroup>
                            <span>-</span>
                            <InputGroup style={{ width: "50%" }}>
                                <FormControl
                                    type={'time'}
                                    key={`${date}_new_interval_${idx}_end`}
                                    value={getTimeStringFromDate(interval?.end)}
                                    name={'end'}
                                    onChange={async (e) => {
                                        await onTimeInputChange(idx, e.target.name, e.target.value)
                                    }}
                                    style={{ textAlign: "center", }}
                                    disabled={!interval?.start}
                                    min={getTimeStringFromDate(interval?.start)}
                                    max={getTimeStringFromDate(endDt)}
                                    required
                                    isInvalid={interval.start !== undefined && (
                                        !isIntervalValid(interval) ||
                                        !isNewIntervalValid(interval, idx)
                                    )}
                                />
                            </InputGroup>
                            <Button
                                variant={'danger'}
                                name={'deleteBtn'}
                                onClick={async () => await onRemoveButtonClick(idx)}
                            >
                                X
                            </Button>
                        </div>
                    )
                })}
            </div>
            {loading
                ? (
                    <div className={'d-flex justify-content-center w-100 mt-3 align-items-center gap-2'}>
                        Создание расписания… Пожалуйста, подождите.
                    </div>
                )
                : (
                    <div className={'d-flex justify-content-center w-100 mt-3 align-items-center gap-2'}>
                        <Button variant={'success'} name={'addIntervalBtn'} onClick={onAddButtonClick}>
                            Добавить рабочий промежуток
                        </Button>
                        <Form.Group className="me-0">
                            <Form.Check
                                type="checkbox"
                                label="Массовое добавление (на 48 недель)"
                                checked={checkbox}
                                onChange={(e) => handleCheckboxChange(e)}
                            />
                        </Form.Group>
                    </div>
                )
            }
        </CustomModal>
    );
}


export default EditNAInterval;