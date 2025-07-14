import React, { useCallback, useMemo, useState, useContext } from 'react';
import useSchedules from "../../hooks/useSchedules.js";
import CustomModal from "../ui/Modal/index.jsx";
import { useDayContext } from "../../contexts/Day/provider.jsx";
import { Button, FormControl, InputGroup, Form } from "react-bootstrap";
import { areIntervalsOverlapping, getDateWithTime, getTimeStringFromDate, isIntervalValid } from "../../utils/dates.js";
import { useSpecialistContext } from "../../contexts/Specialist/provider.jsx";
import apiClient from "../../api/index.js";
import Holidays from 'date-holidays';
import { AppContext } from "../../contexts/App/context.js";

const AddWorkScheduleModal = ({ show, setShow }) => {
    const {
        generalWorkSchedule,
        setGeneralWorkSchedule,
    } = useSchedules();
    const date = useDayContext();
    const specialistId = useSpecialistContext();
    const dayOfWeek = date.toLocaleString('ru-RU', { weekday: 'long' });
    const dateString = date.toLocaleDateString();
    const [workIntervals, setWorkIntervals] = useState([]);
    const holidays = new Holidays('RU');
    const [checkbox, setCheckbox] = useState(false)
    const [loading, setLoading] = useState(false)
    const { dates, setDates } = useContext(AppContext);


    const isNewIntervalValid = useCallback((interval, index) => {
        if (interval.start !== undefined && interval.end !== undefined) {
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
    }, [workIntervals])

    const areIntervalsValid = useMemo(() => {
        return workIntervals.map(isNewIntervalValid).every(elem => elem === true)
    }, [isNewIntervalValid, workIntervals]);

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

    const onAddButtonClick = () => {
        setWorkIntervals([...workIntervals, { start: undefined, end: undefined }])
    }

    const onRemoveButtonClick = async (idx) => {
        setWorkIntervals(workIntervals.filter((value, index) => index !== idx));
    }
    const isHoliday = (date) => {
        const holidaysList = holidays.getHolidays(date.getFullYear());
        return holidaysList.some(holiday => {
            const holidayDate = new Date(holiday.date);
            return holidayDate.toISOString().split('T')[0] === date.toISOString().split('T')[0];
        });
    };

    const handleCheckboxChange = (e) => {
        setCheckbox(e.target.checked);
    };

    const createNewWorkSchedule = async (specialistId, baseDate, workIntervals, repeatWeekly = false) => {
        const schedulesToCreate = [];

        let currentDate = new Date(baseDate);

        if (repeatWeekly) {
            for (let i = 0; i < 48; i++) {
                const isDayOff = isHoliday(currentDate) || currentDate.getDay() === 0;

                if (!isDayOff) {
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
                    }));

                    schedulesToCreate.push({
                        date: new Date(currentDate),
                        intervals: adjustedIntervals
                    });
                }

                currentDate.setDate(currentDate.getDate() + 7);
            }
        } else {
            // Одноразовое расписание
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
            }));

            schedulesToCreate.push({
                date: new Date(currentDate),
                intervals: adjustedIntervals
            });
        }

        const createdSchedules = [];

        for (const schedule of schedulesToCreate) {
            if (repeatWeekly) {
                const result = await apiClient.createWorkScheduleMassive({
                specialist: specialistId,
                date: schedule.date,
                intervals: schedule.intervals
            });
            } else {
                const result = await apiClient.createWorkSchedule({
                specialist: specialistId,
                date: schedule.date,
                intervals: schedule.intervals
            });
            }

            if (result) {
                createdSchedules.push({
                    date: schedule.date.toISOString().split('T')[0],
                    data: {
                        id: result.id,
                        intervals: schedule.intervals
                    }
                });
            }
        }

        return createdSchedules;
    };

    const onSumbit = async () => {
        setLoading(true);

        try {
            const createdSchedules = await createNewWorkSchedule(
                specialistId,
                date,
                workIntervals,
                checkbox
            );

            // Обновляем стейт общего расписания
            setGeneralWorkSchedule(prev => {
                const updatedSpecialistSchedule = createdSchedules.reduce((acc, { date, data }) => {
                    acc[date] = data;
                    return acc;
                }, {});

                return {
                    ...prev,
                    [specialistId]: {
                        ...(prev[specialistId] || {}),
                        ...updatedSpecialistSchedule
                    }
                };
            });

        } catch (error) {
            console.error("Ошибка при создании расписания:", error);
        } finally {
            setLoading(false);
            setDates({ fromDate: new Date(dates.fromDate), toDate: new Date(dates.toDate) });
        }
    };

    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={`${specialistId}, ${dayOfWeek} ${dateString}`}
            primaryBtnDisabled={
                loading ||
                workIntervals.length === 0 ||
                !workIntervals.map(interval => isIntervalValid(interval)).every(elem => elem === true) ||
                !areIntervalsValid
            }
            primaryBtnText={'Сохранить'}
            handlePrimaryBtnClick={onSumbit}
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
};

export default AddWorkScheduleModal;