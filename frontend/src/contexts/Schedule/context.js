import React, {useState} from "react";

export const ScheduleContext = React.createContext([]);

export function useCreateScheduleContext(schedule) {
    const [services, setServices] = useState(schedule);
    return [services, setServices];
}
