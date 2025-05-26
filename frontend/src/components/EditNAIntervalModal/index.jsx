import React, {useCallback, useMemo, useState} from 'react';
import CustomModal from "../ui/Modal/index.jsx";
import {
    areIntervalsOverlapping,
    getDateWithTime,
    getTimeStringFromDate,
    isIntervalValid,
} from "../../utils/dates.js";
import useSchedules from "../../hooks/useSchedules.js";
import {useDayContext} from "../../contexts/Day/provider.jsx";
import useSpecialist from "../../hooks/useSpecialist.js";
import apiClient from "../../api/index.js";
import {Button, FormControl, InputGroup} from "react-bootstrap";

const EditNAInterval = ({show, setShow, startDt, endDt}) => {
    const [workIntervals, setWorkIntervals] = useState([]);
    const [loading, setLoading] = useState(false);
    const {
        generalWorkSchedule,
        setGeneralWorkSchedule,
        workSchedule
    } = useSchedules();
    const date = useDayContext();
    const {specialistId, specialist} = useSpecialist();
    const dayOfWeek = date.toLocaleString('ru-RU', {weekday: 'long'});
    const dateString = date.toLocaleDateString();

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
                return {...interval, [attrName]: getDateWithTime(date, hours, minutes)};
            } else {
                return interval;
            }
        });
        setWorkIntervals(newIntervals);
    }

    const onAddButtonClick = () => {
        setWorkIntervals([...workIntervals, {start: undefined, end: undefined}])
    }

    const onRemoveButtonClick = async (idx) => {
        setWorkIntervals(workIntervals.filter((value, index) => index !== idx));
    }

    const handleSubmit = async () => {
        const newWorkIntervals = [...workSchedule.intervals, ...workIntervals];
        const result = await apiClient.updateWorkSchedule(workSchedule.id, {
            specialist: specialistId, date: date, intervals: newWorkIntervals
        });
        if (result) {
            setGeneralWorkSchedule({
                ...generalWorkSchedule,
                [specialistId]: {
                    ...generalWorkSchedule[specialistId],
                    [date]: {
                        id: workSchedule.id,
                        intervals: newWorkIntervals
                    }
                }
            });
        }
        setLoading(false);
        setShow(false);
    }

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
                            <InputGroup style={{width: "50%"}}>
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
                                    style={{textAlign: "center"}}
                                    required
                                    isInvalid={!interval.start}
                                />
                            </InputGroup>
                            <span>-</span>
                            <InputGroup style={{width: "50%"}}>
                                <FormControl
                                    type={'time'}
                                    key={`${date}_new_interval_${idx}_end`}
                                    value={getTimeStringFromDate(interval?.end)}
                                    name={'end'}
                                    onChange={async (e) => {
                                        await onTimeInputChange(idx, e.target.name, e.target.value)
                                    }}
                                    style={{textAlign: "center",}}
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
            <div className={'d-flex justify-content-center w-100 mt-3'}>
                <Button variant={'success'} name={'addIntervalBtn'} onClick={onAddButtonClick}>
                    Добавить рабочий промежуток
                </Button>
            </div>
        </CustomModal>
    );
}


export default EditNAInterval;