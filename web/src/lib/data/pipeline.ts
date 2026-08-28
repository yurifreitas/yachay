/** One dataset, one module. */
import raw from "../../data/generated/pipeline.json";
import type { PipelineState } from "../pipelineModel";

export const pipeline = raw as unknown as PipelineState;
