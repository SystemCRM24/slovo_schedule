import React, { useContext, useEffect, useMemo, useState } from "react";
import CustomModal from "../ui/Modal/index.jsx";
import { FormControl, FormSelect, InputGroup } from "react-bootstrap";

import { AppContext } from "../../contexts/App/context.js";
import { useAllSpecialistsContext } from "../../contexts/AllSpecialists/provider.jsx";
import useSchedules from "../../hooks/useSchedules.js";
import useSpecialist from "../../hooks/useSpecialist.js";
import { getDateWithTime, getISODate, getTimeStringFromDate, isIntervalValid, isNewScheduleIntervalValid } from "../../utils/dates.js";
import apiClient from "../../api/index.js";

const EditClientInfoModal = ({ id, show, setShow }) => {
    const {
        schedule: appointmentsOfDay,
        workSchedule: schedulesOfDay,
        generalSchedule: appointments,
        generalWorkSchedule: schedules,
        setGeneralSchedule: setAppointments,
        setGeneralWorkSchedule: setSchedules
    } = useSchedules();

    const appointment = useMemo(
        () => {
            for (const appointment of appointmentsOfDay) {
                if (appointment.id === id) {
                    return appointment;
                }
            }
        },
        [id, appointmentsOfDay]
    );

    const specialists = useAllSpecialistsContext();
    const specialistsOptions = useMemo(
        () => {
            return Object.entries(specialists)
                .sort(([a, aIndex], [b, bIndex]) => aIndex.sort_index - bIndex.sort_index)
                .map(
                    ([id, spec]) => {
                        return (
                            <option value={id} key={`specialist_${id}`}>
                                {spec.name} ({spec.departments.join(', ')})
                            </option>
                        );
                    }
                );
        },
        [specialists]
    );

    const [specialist, setSpecialist] = useState(useSpecialist());
    const onSpecialistChange = (e) => {
        for (const specialist of Object.values(specialists)) {
            if (e.target.value == specialist.id) {
                setSpecialist({
                    specialistId: parseInt(e.target.value),
                    specialist
                });
                break;
            }
        }
    };

    const [start, setStart] = useState(appointment.start);
    const [end, setEnd] = useState(appointment.end);

    const specialistScheduleOfDay = useMemo(
        () => {
            const [s_year, s_month, s_day] = [start.getFullYear(), start.getMonth(), start.getDate()];
            const scheduleOfSpecialist = schedules[specialist.specialistId];
            if (scheduleOfSpecialist) {
                for (const [dateStr, schedule] of Object.entries(scheduleOfSpecialist)) {
                    const date = new Date(dateStr);
                    const [c_year, c_month, c_day] = [date.getFullYear(), date.getMonth(), date.getDate()];
                    if (s_year == c_year && s_month == c_month && s_day == c_day) {
                        return schedule;
                    }
                }
            }
            return null;
        },
        [specialist, start, schedules]
    );

    const spesialistAppointmentsOfDay = useMemo(
        () => {
            const [s_year, s_month, s_day] = [start.getFullYear(), start.getMonth(), start.getDate()];
            const appointmentsOfSpecialist = appointments[specialist.specialistId];
            if (appointmentsOfSpecialist) {
                for (const [dateStr, apps] of Object.entries(appointmentsOfSpecialist)) {
                    const date = new Date(dateStr);
                    const [c_year, c_month, c_day] = [date.getFullYear(), date.getMonth(), date.getDate()];
                    if (s_year == c_year && s_month == c_month && s_day == c_day) {
                        return apps;
                    }
                }
            }
            return null;
        },
        [specialist, start, appointments]
    );

    const [date, setDate] = useState(getISODate(start));
    const onDateChange = (e) => {
        const value = e.target.value;
        if (!value) {
            return;
        }
        const date = new Date(e.target.value);
        const newStart = new Date(start);
        newStart.setFullYear(date.getFullYear(), date.getMonth(), date.getDate());
        setStart(newStart);
        setDate(getISODate(date));
    };

    const [dateIsInvalid, setDateIsInvalid] = useState(true);
    // подсчет валидности даты
    useEffect(
        () => setDateIsInvalid(specialistScheduleOfDay == null),
        [specialistScheduleOfDay]
    );

    const [startTime, setStartTime] = useState(getTimeStringFromDate(appointment.start));
    const onStartTimeChange = (e) => {
        const value = e.target.value;
        if (value) {
            const [hoursString, minutesString] = value.split(':');
            const hours = parseInt(hoursString);
            const minutes = parseInt(minutesString);
            const newStart = getDateWithTime(start, hours, minutes);
            setStart(newStart);
        }
        setStartTime(value);
        setStartTime(e.target.value);
    };

    const [startIsInvalid, setStartIsInvalid] = useState(true);
    // Подсчет валидности старта
    useEffect(
        () => {
            let inSchedule = false;
            if (specialistScheduleOfDay !== null) {
                for (const interval of specialistScheduleOfDay.intervals) {
                    if (interval.start <= start && start < interval.end) {
                        inSchedule = true;
                        break;
                    }
                }
            }
            let notInAppointment = true;
            if (spesialistAppointmentsOfDay !== null) {
                for (const otherAppointment of spesialistAppointmentsOfDay) {
                    if (otherAppointment.id !== id) {
                        if (otherAppointment.start <= start && start < otherAppointment.end) {
                            notInAppointment = false;
                            break;
                        }
                    }
                }
            }
            setStartIsInvalid(!(inSchedule && notInAppointment));
        },
        [specialistScheduleOfDay, start, spesialistAppointmentsOfDay, setStartIsInvalid]
    );

    const durationValues = useMemo(() => [15, 30, 45, 60, 90, 120, 130], []);
    const durationOptions = useMemo(
        () => {
            const options = durationValues.map(
                (value) => (
                    <option value={value} key={`duration_${value}`}>
                        {value} минут
                    </option>
                )
            );
            return options;
        },
        [durationValues]
    );

    const [duration, setDuration] = useState((end - start) / 60000);
    // Пересчет end, когда меняется duration или start
    useEffect(
        () => setEnd(new Date(start.getTime() + duration * 60000)),
        [start, duration]
    );

    const [durationIsInvalid, setDurationsIsInvalid] = useState(true);
    useEffect(
        () => {
            let inSchedule = false;
            if (specialistScheduleOfDay !== null) {
                for (const interval of specialistScheduleOfDay.intervals) {
                    if (interval.start < end && end <= interval.end) {
                        inSchedule = true;
                        break;
                    }
                }
            }
            let notInAppointment = true;
            if (spesialistAppointmentsOfDay !== null) {
                for (const otherAppointment of spesialistAppointmentsOfDay) {
                    if (otherAppointment.id !== id) {
                        if (otherAppointment.start < end && end <= otherAppointment.end) {
                            notInAppointment = false;
                            break;
                        }
                    }
                }
            }
            setDurationsIsInvalid(!(inSchedule && notInAppointment));
        },
        [specialistScheduleOfDay, end, spesialistAppointmentsOfDay, setDurationsIsInvalid]
    );

    const { dates, setDates } = useContext(AppContext);
    const onSubmit = async () => {
        const currentSpecialistId = specialist.specialistId;
        const updatedAppointment = structuredClone(appointment);
        updatedAppointment.start = start;
        updatedAppointment.end = end;
        const data = {
            id: updatedAppointment.id,
            specialist: currentSpecialistId,
            patient: updatedAppointment.patient.id,
            start: updatedAppointment.start,
            end: updatedAppointment.end,
            code: updatedAppointment.patient.type,
            old_patient: updatedAppointment.old_patient
        };
        const result = await apiClient.updateAppointment(updatedAppointment.id, data);
        setShow(false);
        setDates({ fromDate: new Date(dates.fromDate), toDate: new Date(dates.toDate) });
    };

    return (
        <CustomModal
            show={show}
            title={`Перенос занятия`}
            primaryBtnDisabled={dateIsInvalid || startIsInvalid || durationIsInvalid}
            primaryBtnText={'Перенести'}
            handlePrimaryBtnClick={onSubmit}
            handleClose={() => setShow(false)}
        >
            <div className="d-flex flex-column align-items-center justify-content-center w-100 h-100 gap-2">
                <label>Исполнитель</label>
                <InputGroup hasValidation>
                    <FormSelect
                        name={'specialist'}
                        isInvalid={dateIsInvalid || startIsInvalid || durationIsInvalid}
                        onChange={onSpecialistChange}
                        value={specialist.specialistId}
                    >
                        <option disabled value="">Выберите специалиста</option>
                        {specialistsOptions}
                    </FormSelect>
                </InputGroup>
                <div className="d-flex w-100 align-items-center" style={{ gap: "1rem", whiteSpace: "nowrap" }}>
                    <label>Дата занятия</label>
                    <InputGroup hasValidation>
                        <FormControl
                            type={'date'}
                            value={date}
                            name={'day'}
                            onChange={onDateChange}
                            style={{ textAlign: "center" }}
                            required
                            isInvalid={dateIsInvalid}
                        />
                    </InputGroup>
                    <label>Начало занятия</label>
                    <InputGroup hasValidation>
                        <FormControl
                            type={'time'}
                            value={startTime}
                            name={'start'}
                            onChange={onStartTimeChange}
                            style={{ textAlign: "center" }}
                            required
                            isInvalid={startIsInvalid}
                        />
                    </InputGroup>
                    <label>Продолжительность</label>
                    <InputGroup hasValidation>
                        <FormControl
                            as={'select'}
                            style={{ textAlign: "center" }}
                            required
                            value={duration}
                            onChange={(e) => setDuration(parseInt(e.target.value))}
                            isInvalid={durationIsInvalid}
                        >
                            {durationOptions}
                        </FormControl>
                    </InputGroup>
                </div>
            </div>
        </CustomModal>
    );
};

export default EditClientInfoModal;
