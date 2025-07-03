import React, { useCallback, useMemo, useState } from 'react';
import useSchedules from "../../hooks/useSchedules.js";
import CustomModal from "../ui/Modal/index.jsx";
import { useDayContext } from "../../contexts/Day/provider.jsx";
import { Button, FormControl, InputGroup } from "react-bootstrap";
import { areIntervalsOverlapping, getDateWithTime, getTimeStringFromDate, isIntervalValid } from "../../utils/dates.js";
import { useSpecialistContext } from "../../contexts/Specialist/provider.jsx";
import apiClient from "../../api/index.js";
import Holidays from 'date-holidays';

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

    const onSumbit = async () => {
        let currentDate = new Date(date);
        const newSchedules = [];

        for (let i = 0; i <= 2; i++) {
            if (i > 0 && isHoliday(currentDate)) {
                currentDate = new Date(currentDate.getTime() + 7 * 24 * 60 * 60 * 1000);
                continue;
            }
            const result = await apiClient.createWorkSchedule({
                specialist: specialistId,
                date: currentDate,
                intervals: workIntervals,
            });

            if (result) {
                newSchedules.push({
                    date: currentDate,
                    data: { id: result?.id, intervals: workIntervals }
                });
            }

            currentDate = new Date(currentDate.getTime() + 7 * 24 * 60 * 60 * 1000);
        }

        setGeneralWorkSchedule(prevSchedule => ({
            ...prevSchedule,
            [specialistId]: {
                ...(prevSchedule[specialistId] || {}),
                ...newSchedules.reduce((acc, { date, data }) => {
                    acc[date] = data;
                    return acc;
                }, {})
            }
        }));
    };

    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={`${specialistId}, ${dayOfWeek} ${dateString}`}
            primaryBtnDisabled={
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
            <div className={'d-flex justify-content-center w-100 mt-3'}>
                <Button variant={'success'} name={'addIntervalBtn'} onClick={onAddButtonClick}>
                    Добавить рабочий промежуток
                </Button>
            </div>
        </CustomModal>
    );
};

export default AddWorkScheduleModal;