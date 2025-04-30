import React from "react";
import {DayContext} from "./context.js";

export function DayContextProvider({children, day}) {
    return <DayContext.Provider value={day}>{children}</DayContext.Provider>
}

/**
 *
 * @returns {Date}
 */
export function useDayContext() {
    const context = React.useContext(DayContext);
    if (!context) throw new Error('Use context within provider!');
    return context;
}
