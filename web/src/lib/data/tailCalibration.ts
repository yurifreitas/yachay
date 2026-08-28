/** One dataset, one module. */
import raw from "../../data/generated/tail_calibration.json";
import type { TailCalibration } from "../tailCalibrationModel";

export const tailCalibration = raw as unknown as TailCalibration;
