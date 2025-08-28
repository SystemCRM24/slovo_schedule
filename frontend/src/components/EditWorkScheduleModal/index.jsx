import React, { useCallback, useEffect, useMemo, useState, useContext } from 'react';
import CustomModal from "../ui/Modal/index.jsx";
import useSchedules from "../../hooks/useSchedules.js";
import { useDayContext } from "../../contexts/Day/provider.jsx";
import {
    findScheduleIntervalsInRange,
    getDateWithTime, isNewWorkScheduleValidModify,
    getTimeStringFromDate, areIntervalsOverlapping,
    isIntervalValid, isNewScheduleValid, isNewScheduleIntervalValid, isNewWorkScheduleValid
} from "../../utils/dates.js";
import { Button, FormControl, FormSelect, InputGroup, Form } from "react-bootstrap";
import useSpecialist from "../../hooks/useSpecialist.js";
import { useChildrenContext } from "../../contexts/Children/provider.jsx";
import apiClient, { constants } from "../../api/index.js";
import AutoCompleteInput from "../../components/ui/AutoCompleteInput/index.jsx";
import { AppContext } from '../../contexts/App/context.js';
import { Right, Left} from './icons.jsx';



const EditWorkScheduleModal = ({ show, setShow, startDt, endDt }) => {
    const [newSchedules, setNewSchedules] = useState([]);
    const [loading, setLoading] = useState(false);
    const [workInterval, setWorkInterval] = useState({ start: startDt, end: endDt });
    const {
        generalSchedule,
        generalWorkSchedule,
        setGeneralSchedule,
        setGeneralWorkSchedule,
        schedule,
        workSchedule
    } = useSchedules();
    const { specialist, specialistId } = useSpecialist();
    const date = useDayContext();
    const children = useChildrenContext();
    const dayOfWeek = date.toLocaleString('ru-RU', { weekday: 'long' });
    const dateString = date.toLocaleDateString();

    const findIntervalPredicate = useCallback((interval) => {
        return interval.start.getTime() <= startDt.getTime() && interval.end.getTime() >= endDt.getTime()
    }, [startDt, endDt]);

    const [realInterval, realIntervalIndex] = useMemo(() => {
        return [workSchedule.intervals.find(findIntervalPredicate), workSchedule.intervals.findIndex(findIntervalPredicate)]
    }, [workSchedule, findIntervalPredicate]);

    useEffect(() => {
        setWorkInterval(realInterval);
    }, [realInterval]);

    const canDelete = useMemo(() => {
        const schedules = findScheduleIntervalsInRange(
            schedule, realInterval.start.getTime(), realInterval.end.getTime()
        );
        return schedules.length === 0;
    }, [realInterval, schedule]);

    const onTimeInputChange = async (idx, attrName, value) => {
        const newIntervals = newSchedules.map((schedule, index) => {
            if (index === idx) {
                return { ...schedule, [attrName]: value };
            } else {
                return schedule;
            }
        });
        setNewSchedules(newIntervals);
    }

    const handleIntervalChange = async (e) => {
        const [hoursString, minutesString] = e.target.value.split(':');
        const hours = parseInt(hoursString);
        const minutes = parseInt(minutesString);
        let value = getDateWithTime(date, hours, minutes);
        setWorkInterval({ ...workInterval, [e.target.name]: value })
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
            status: 'Единичное',
            old_patient: undefined
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
                return isNewScheduleValid(newSchedule, newSchedulesWithoutCurrentElem, schedule, workInterval);
            })
            .every(item => item === true);
    }, [newSchedules, schedule, workInterval]);

    const isWorkScheduleValid = useMemo(() => {
        const workScheduleWithoutCurrentInterval = workSchedule.intervals
            .filter((value, index) => index !== realIntervalIndex);
        return isNewWorkScheduleValidModify(workInterval, newSchedules, schedule, workScheduleWithoutCurrentInterval);
    }, [newSchedules, realIntervalIndex, schedule, workInterval, workSchedule.intervals]);

    const {decreaseModalCount, reloadSchedule} = useContext(AppContext);

    const handleDelete = async () => {
        const newWorkScheduleIntervals = workSchedule.intervals.filter(
            (value, index) => index !== realIntervalIndex
        );
        if (newWorkScheduleIntervals.length === 0) {
            await apiClient.deleteWorkSchedule(workSchedule.id);
            const newGeneralWorkSchedule = structuredClone(generalWorkSchedule);
            delete newGeneralWorkSchedule[specialistId][date];
            setGeneralWorkSchedule(newGeneralWorkSchedule);
        } else {
            const result = await apiClient.updateWorkSchedule(workSchedule.id, {
                specialist: specialistId, date: date, intervals: newWorkScheduleIntervals
            });
            if (result) {
                setGeneralWorkSchedule({
                    ...generalWorkSchedule,
                    [specialistId]: {
                        ...generalWorkSchedule[specialistId],
                        [date]: {
                            id: workSchedule.id,
                            intervals: newWorkScheduleIntervals
                        }
                    }
                });
            }
        }
        decreaseModalCount();
        setShow(false);
    }

    const handleSubmit = async () => {
        setLoading(true);
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
        const newWorkIntervals = workSchedule.intervals.map((value, index) => {
            if (index === realIntervalIndex) {
                return workInterval;
            } else {
                return value;
            }
        });
        const response = {specialist: specialistId, date: date, intervals: newWorkIntervals};
        if ( checkbox ) {
            const result = await apiClient.updateWorkScheduleMassive(workSchedule.id, response);
        } else {
            const result = await apiClient.updateWorkSchedule(workSchedule.id, response);
        }
        let tasks = [];
        for (const appointment of transformedNewSchedules) {
            tasks.push(apiClient.createAppointment(appointment));
        }
        const results = await Promise.all(tasks);
        for (const [index, sched] of Object.entries(results)) {
            sched.patient = {id: sched.patient, type: sched.code};
            sched.start = new Date(sched.start);
            sched.end = new Date(sched.end);
            sched.old_start = new Date(sched.old_start);
            sched.old_end = new Date(sched.old_end);
            transformedNewSchedules[index] = sched;
        }
        reloadSchedule();
        decreaseModalCount();
        setLoading(false);
        setShow(false);
    }

    const selectOptions = useMemo(
        () => {
            const defaultSelectValues = [30, 40, 60, 90];
            return defaultSelectValues.map(
                (value) => (<option key={value + '_option'} value={value}>{value} минут</option>)
            );
        },
        []
    );

    const handleSelectInputChange = async (e, idx) => {
        const ms = e.target.value * 60 * 1000;
        let currentSchedule;
        newSchedules.forEach(
            (value, index) => {
                if (index == idx) {
                    currentSchedule = value;
                }
            }
        );
        const end = new Date(currentSchedule.start.getTime() + ms);
        onTimeInputChange(idx, e.target.name, end);
    };

    const selectValues = useMemo(
        () => {
            return newSchedules.map(
                (newSchedule) => {
                    if (newSchedule.start && newSchedule.end) {
                        return (newSchedule.end - newSchedule.start) / 60000;
                    }
                    return '';
                }
            );
        },
        [newSchedules]
    );

    const [checkbox, setCheckbox] = useState(false);

    const [showTimeInput, setShowTimeInput] = useState(false);

    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={`${specialist.name} - ${dayOfWeek} ${dateString} ${getTimeStringFromDate(workInterval.start)}
             - ${getTimeStringFromDate(workInterval.end)}`}
            handlePrimaryBtnClick={handleSubmit}
            primaryBtnText={'Сохранить'}
            primaryBtnDisabled={!areNewSchedulesValid || !isWorkScheduleValid || loading}
        >
            <div className="d-flex flex-column align-items-center justify-content-center w-100 h-100 gap-2">
                <div className="d-flex gap-2 flex-end mb-4" style={{width: '100%'}}>
                    <div 
                        className="d-flex align-items-center justify-content-center" 
                        style={{width: '100%'}}
                    >
                        {showTimeInput && 
                            <>
                                <InputGroup hasValidation>
                                    <FormControl
                                        type={'time'}
                                        key={`${date}_interval_${realIntervalIndex}_start`}
                                        value={getTimeStringFromDate(workInterval.start)}
                                        name={'start'}
                                        onChange={handleIntervalChange}
                                        style={{ textAlign: "center" }}
                                        required
                                        isInvalid={
                                            !workInterval.start || !isWorkScheduleValid
                                        }
                                    />
                                </InputGroup>
                                <span>-</span>
                                <InputGroup hasValidation>
                                    <FormControl
                                        type={'time'}
                                        key={`${date}_interval_${realIntervalIndex}_end`}
                                        value={getTimeStringFromDate(workInterval.end)}
                                        name={'end'}
                                        onChange={handleIntervalChange}
                                        style={{ textAlign: "center", }}
                                        disabled={!workInterval.start}
                                        min={getTimeStringFromDate(workInterval.start)}
                                        required
                                        isInvalid={
                                            workInterval.start !== undefined && (!isIntervalValid(workInterval) || !isWorkScheduleValid)
                                        }
                                    />
                                </InputGroup>
                            </>
                        }
                    </div>
                    <Button
                        variant='warning'
                        onClick={() => setShowTimeInput(!showTimeInput)}
                    >
                        {showTimeInput ? <Right/> : <Left/>}
                    </Button>
                </div>
                <Button 
                    variant={'danger'} 
                    onClick={handleDelete} 
                    // disabled={!canDelete}
                >
                    Удалить рабочий промежуток
                </Button>
                {!canDelete && 
                    <div className={'text-danger opacity-50'}>
                        Удалите или перенесите занятия внутри рабочего промежутка для его удаления
                    </div>
                }
                {(!isIntervalValid(workInterval) || !isWorkScheduleValid)&& 
                    <div className={'text-danger opacity-50'}>
                        Промежутки рабочего времени наслаиваются друг на друга.
                    </div>
                }
                <Button variant={'success'} onClick={onAddButtonClick}>Добавить занятие</Button>
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
                                    style={{ textAlign: "center" }}
                                    min={getTimeStringFromDate(startDt)}
                                    max={getTimeStringFromDate(endDt)}
                                    required
                                    isInvalid={
                                        !newSchedule.start ||
                                        (
                                            !!newSchedule.start
                                            && !isNewScheduleIntervalValid(newSchedule, newSchedulesWithoutCurrentElem, schedule, workInterval)
                                        )
                                    }
                                />
                            </InputGroup>
                            <span>-</span>
                            <InputGroup hasValidation>
                                <FormSelect
                                    name={'end'}
                                    style={{ textAlign: "center", }}
                                    disabled={!newSchedule.start}
                                    required
                                    value={selectValues[idx]}
                                    onChange={async e => await handleSelectInputChange(e, idx)}
                                    isInvalid={
                                        newSchedule.start !== undefined &&
                                        (
                                            !isIntervalValid(newSchedule) ||
                                            !isNewScheduleIntervalValid(newSchedule, newSchedulesWithoutCurrentElem, schedule, workInterval)
                                        )
                                    }
                                >
                                    <option disabled value={''}>Выберите длительность</option>
                                    {selectOptions}
                                </FormSelect>
                            </InputGroup>
                            <InputGroup hasValidation>
                                <AutoCompleteInput
                                    options={children}
                                    name={'patientId'}
                                    isInvalid={['', null, undefined].includes(newSchedule.patientId)}
                                    onChange={async (e) => {
                                        await handleInputChange(e, idx);
                                    }}
                                    value={newSchedule.patientId}
                                />
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
                                    {Object.entries(constants.listFieldValues.appointment.idByCode)
                                        .sort(([aCode], [bCode]) => aCode.localeCompare(bCode, 'en', { sensitivity: 'base' }))
                                        .map(([code, id]) => {
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

export default EditWorkScheduleModal;