import React, {useState} from "react";

export const ScheduleContext = React.createContext([]);

export function useCreateScheduleContext(initialSchedule) {
    const [schedule, setSchedule] = useState(initialSchedule);
    return [schedule, setSchedule];
}
