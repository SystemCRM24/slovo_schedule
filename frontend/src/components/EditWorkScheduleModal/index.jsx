import React, {useCallback, useMemo, useState} from 'react';
import CustomModal from "../ui/Modal/index.jsx";
import useSchedules from "../../hooks/useSchedules.js";
import {useDayContext} from "../../contexts/Day/provider.jsx";
import {
    findScheduleIntervalsInRange,
    getDateWithTime,
    getTimeStringFromDate, areIntervalsOverlapping,
    isIntervalValid, isNewScheduleValid, isScheduleValid
} from "../../utils/dates.js";
import {Button, FormControl, FormSelect, InputGroup} from "react-bootstrap";
import useSpecialist from "../../hooks/useSpecialist.js";
import {useChildrenContext} from "../../contexts/Children/provider.jsx";
import apiClient, {constants} from "../../api/index.js";

const EditWorkScheduleModal = ({show, setShow, startDt, endDt}) => {
    const [newSchedules, setNewSchedules] = useState([]);
    const {
        generalSchedule,
        generalWorkSchedule,
        setGeneralSchedule,
        setGeneralWorkSchedule,
        schedule,
        workSchedule
    } = useSchedules();
    const {specialist, specialistId} = useSpecialist();
    const date = useDayContext();
    const children = useChildrenContext();
    const dayOfWeek = date.toLocaleString('ru-RU', {weekday: 'long'});
    const dateString = date.toLocaleDateString();

    const findIntervalPredicate = useCallback((interval) => {
        return interval.start.getTime() <= startDt.getTime() && interval.end.getTime() >= endDt.getTime()
    }, [startDt, endDt]);

    const [realInterval, realIntervalIndex] = useMemo(() => {
        return [workSchedule.intervals.find(findIntervalPredicate), workSchedule.intervals.findIndex(findIntervalPredicate)]
    }, [workSchedule, findIntervalPredicate]);

    const onTimeInputChange = async (idx, attrName, value) => {
        const newIntervals = newSchedules.map((schedule, index) => {
            if (index === idx) {
                return {...schedule, [attrName]: value};
            } else {
                return schedule;
            }
        });
        setNewSchedules(newIntervals);
    }

    const handleInputChange = async (e, idx) => {
        let value;
        if (['start', 'end'].includes(e.target.name)) {
            const [hoursString, minutesString] = e.target.value.split(':');
            const hours = parseInt(hoursString);
            const minutes = parseInt(minutesString);
            value = getDateWithTime(date, hours, minutes);
        } else {
            value = e.target.value;
        }
        await onTimeInputChange(idx, e.target.name, value)
    }

    const onAddButtonClick = async () => {
        setNewSchedules([...newSchedules, {
            start: undefined,
            end: undefined,
            patientId: undefined,
            patientType: undefined,
            status: 'booked'
        }]);
    }

    const onRemoveButtonClick = async (idx) => {
        setNewSchedules(newSchedules.filter((value, index) => index !== idx));
    }

    const areNewSchedulesValid = useMemo(() => {
        return newSchedules
            .map((newSchedule, idx) => {
                const newSchedulesWithoutCurrentElem =
                    newSchedules.filter((item, index) => index !== idx);
                return isNewScheduleValid(newSchedule, newSchedulesWithoutCurrentElem, schedule, realInterval);
            })
            .every(item => item === true);
    }, [newSchedules, realInterval, schedule]);

    const handleSubmit = async () => {
        setShow(false);
        let transformedNewSchedules = newSchedules.map(item => {
            return {
                start: item.start,
                end: item.end,
                status: item.status,
                code: item.patientType,
                patient: item.patientId,
                specialist: specialistId,
            }
        });
        console.log(transformedNewSchedules);
        let tasks = [];
        for (const appointment of transformedNewSchedules) {
            tasks.push(apiClient.createAppointment(appointment));
        }
        const results = await Promise.all(tasks);
        for (const [index, sched] of Object.entries(results)) {
            transformedNewSchedules[index] = {
                ...transformedNewSchedules[index],
                id: sched.id,
                patient: {
                    id: transformedNewSchedules[index].patient,
                    type: transformedNewSchedules[index].code,
                }
            }
        }
        console.log(transformedNewSchedules);
        setGeneralSchedule({
            ...generalSchedule,
            [specialistId]: {
                ...generalSchedule[specialistId],
                [date]: [...schedule, ...transformedNewSchedules],
            }
        });
    }

    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={`${specialist.name} - ${dayOfWeek} ${dateString} ${getTimeStringFromDate(startDt)} - ${getTimeStringFromDate(endDt)}`}
            handlePrimaryBtnClick={handleSubmit}
            primaryBtnText={'Сохранить'}
            primaryBtnDisabled={newSchedules.length === 0 || !areNewSchedulesValid}
        >
            <div className="d-flex flex-column align-items-center justify-content-center w-100 h-100 gap-2">
                <Button variant={'success'} onClick={async () => await onAddButtonClick()}>Добавить занятие</Button>
                {newSchedules.map((newSchedule, idx) => {
                    const newSchedulesWithoutCurrentElem =
                        newSchedules.filter((item, index) => index !== idx);
                    return (
                        <div
                            className="d-flex justify-content-between align-items-center gap-3 w-100"
                            key={`${startDt}_${endDt}_new_interval_schedule_${idx}`}
                        >
                            <InputGroup hasValidation>
                                <FormControl
                                    type={'time'}
                                    key={`${date}_new_interval_${idx}_start`}
                                    value={getTimeStringFromDate(newSchedule.start)}
                                    name={'start'}
                                    onChange={async (e) => {
                                        await handleInputChange(e, idx);
                                    }}
                                    style={{textAlign: "center"}}
                                    min={getTimeStringFromDate(startDt)}
                                    max={getTimeStringFromDate(endDt)}
                                    required
                                    isInvalid={
                                        !newSchedule.start ||
                                        (
                                            !!newSchedule.start
                                            && !isScheduleValid(newSchedule, newSchedulesWithoutCurrentElem, schedule, realInterval)
                                        )
                                    }
                                />
                            </InputGroup>
                            <span>-</span>
                            <InputGroup hasValidation>
                                <FormControl
                                    type={'time'}
                                    key={`${date}_new_interval_${idx}_end`}
                                    value={getTimeStringFromDate(newSchedule.end)}
                                    name={'end'}
                                    onChange={async (e) => {
                                        await handleInputChange(e, idx);
                                    }}
                                    style={{textAlign: "center",}}
                                    disabled={!newSchedule.start}
                                    min={getTimeStringFromDate(newSchedule.start)}
                                    max={getTimeStringFromDate(endDt)}
                                    required
                                    isInvalid={
                                        newSchedule.start !== undefined &&
                                        (
                                            !isIntervalValid(newSchedule) ||
                                            !isScheduleValid(newSchedule, newSchedulesWithoutCurrentElem, schedule, realInterval)
                                        )
                                    }
                                />
                            </InputGroup>
                            <InputGroup hasValidation>
                                <FormSelect
                                    name={'patientId'}
                                    isInvalid={['', null, undefined].includes(newSchedule.patientId)}
                                    onChange={async (e) => {
                                        await handleInputChange(e, idx);
                                    }}
                                    value={newSchedule.patientId}
                                >
                                    <option disabled value={undefined} selected>Выберите пациента</option>
                                    {Object.entries(children).map(([childId, childName]) => {
                                        return (
                                            <option value={childId} key={`${date}_new_interval_${idx}_${childId}`}>
                                                {childName}
                                            </option>
                                        );
                                    })}
                                </FormSelect>
                            </InputGroup>
                            <InputGroup hasValidation>
                                <FormSelect
                                    name={'patientType'}
                                    isInvalid={['', null, undefined].includes(newSchedule.patientType)}
                                    onChange={async (e) => {
                                        await handleInputChange(e, idx);
                                    }}
                                    value={newSchedule.patientType}
                                >
                                    <option disabled value={undefined} selected>Выберите услугу</option>
                                    {Object.entries(constants.listFieldValues.appointment.idByCode).map(([code, id]) => {
                                        return (
                                            <option value={code} key={`${date}_interval_${idx}_${code}_opt`}>
                                                {code}
                                            </option>
                                        );
                                    })}
                                </FormSelect>
                            </InputGroup>
                            <Button
                                variant={'danger'}
                                name={'deleteBtn'}
                                onClick={async () => await onRemoveButtonClick(idx)}
                            >
                                X
                            </Button>
                        </div>
                    );
                })}
            </div>
        </CustomModal>
    );
};

export default React.memo(EditWorkScheduleModal);