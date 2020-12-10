
const apispecyaml = `
################################################################################
openapi: 3.0.1
info:
  title: OCPS Job Manager API
  description: "Rubin OCS Controlled Pipeline System (OCPS) Job Management API"
  version: 0.1.0
# servers:
# - url: /api/v1/
#   description: API endpoint base path
tags:
- name: Jobs
  description: Manage jobs
- name: Schemas
  description: Manage job schemas
paths:
  /job:
    put:
      tags:
      - Jobs
      summary: Submit a new job
      description: ""
      operationId: newJob
      requestBody:
        description: |
          **Job specification**

          The schema of the \`config\` property of the job specification is variable; it depends on the job type and that type's associated schema. The structure of the \`config\` property is defined by the schema, which can be fetched via [GET /schema/{job_type}](#/Schemas/getSchema)
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/PutJob"
        required: true
      responses:
        "200":
          description: Job submission status and ID
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PutJobResponse"
        "400":
          description: Invalid syntax
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
  "/job/{job_id}":
    get:
      tags:
      - Jobs
      summary: Request status of an existing job
      operationId: listJobs
      parameters:
      - name: job_id
        in: path
        description: ID of job to return
        required: true
        schema:
          type: string
      responses:
        "200":
          description: successful operation
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GetJob"
        "400":
          description: Invalid ID supplied
        "404":
          description: Job not found
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
    delete:
      tags:
      - Jobs
      summary: Delete an existing job
      description: ""
      operationId: deleteJob
      parameters:
      - name: job_id
        in: path
        description: ID of job to delete
        required: true
        schema:
          type: string
      responses:
        "200":
          description: successful operation
        "400":
          description: Invalid ID supplied
        "404":
          description: Job not found
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
  "/job/list/{category}":
    get:
      tags:
      - Jobs
      summary: Fetch a list of submitted jobs
      operationId: statusJob
      parameters:
      - in: path
        name: category
        required: true
        description: >
            What jobs to list:
             * \`all\` - All jobs
             * \`complete\` - Completed jobs
             * \`pending\` - Pending jobs
             * \`running\` - Running jobs
        schema:
          $ref: '#/components/schemas/ListJobCategories'
      responses:
        "200":
          description: successful operation
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ListJobResponse"
        "400":
          description: Invalid category supplied
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
  /schema/all:
    get:
      tags:
      - Schemas
      summary: Get the schemas for all job types
      operationId: getAllSchema
      responses:
        "200":
          description: successful operation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListSchemaAllResponse'
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
  "/schema/{job_type}":
    get:
      tags:
      - Schemas
      summary: Get the schema for one or all job types
      operationId: getSchema
      parameters:
      - name: job_type
        in: path
        description: Name of job type. 
        required: false
        schema:
          type: string
          example: "ap"
      responses:
        "200":
          description: successful operation
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ListSchemaResponse'
        "404":
          description: Schema for job type not found.
        "500":
          description: error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/GenericServerError"
components:
  schemas:
    ListSchemaResponse:
      type: object
      properties:
        name:
          type: string
          description: Name of job type
          example: "pipeline"
        repo_url:
          type: string
          description: URL of git repo containing the script to be executed 
          example: "https://example.com/org/reponame.git"
        version:
          type: string
          description: Latest stable version (obey semantic versioning spec)
          example: "v2.5.1"
        config:
          type: string
          description: YAML-formatted, descriptive example of configuration data structure specific to the job type
          example: |
            # Name of pipeline to run
            name:
            # Version of pipeline to run
            version:
            # Config overrides. A list of key=value entries, that become -c key=value arguments to pipetask
            config_overrides:
            - key: keyname1
              val: val1
            - key: keyname2
              val: val2
            # Filename overrides that become -C filename arguments to pipetask. Any config filenames are in the same git repo with the same ref as the pipeline YAML.
            filenames:
              - filename1
              - filename2
            # Data selection expression. An expression that is passed as -d query to pipetask.
            data_query: |
              SELECT * FROM DATA_TABLE;
        env:
          type: array
          description: Environment variables
          items:
            type: object
            properties:
              name:
                type: string
                description: Name of environment variable
                example: "IMG_SIZE"
              units:
                type: string
                description: Units of environment variable value
                example: "arcminutes"
              default:
                type: string
                description: Default value of environment variable
                example: "1.0"
              min:
                type: string
                description: Minimum value of environment variable (if applicable)
                example: "0.1"
              max:
                type: string
                description: Maximum value of environment variable (if applicable)
                example: "12.0"
        # TODO: how to describe dynamic object properties?
    ListSchemaAllResponse:
      type: array
      items:
        $ref: "#/components/schemas/ListSchemaResponse"
    GenericServerError:
      type: object
      properties:
        message:
          type: string
          description: Explanation of error
          example: "Error due to XYZ"
    ListJobCategories:
      type: string
      enum:
      - "all"
      - "completed"
      - "pending"
      - "running"
      - "null"
    ListJobResponse:
      type: object
      properties:
        job_ids:
          type: array
          description: List of job IDs
          items:
            type: string
            description: job ID
            example: "c2c5484c22a8434aa301e4f56d17d595"
    PutJob:
      type: object
      properties:
        type:
          type: string
          description: Job type
          example: "pipeline"
        version:
          type: string
          description: Version of the job executable to run
          example: "v2.1.0"
        config:
          type: object
          description: Configuration specific to target job type
          # TODO: Should the input config be YAML-formatted text instead?
          example: {
              "name": "DiaPipelineTask",
              "version": "v20.0.0",
              "config_overrides": [
                  {
                    "key": "firstname",
                    "val": "john"
                  },
                  {
                    "key": "lastname",
                    "val": "smith"
                  }
                ],
              "filenames": [
                "filename1",
                "filename2"
              ],
              "data_query": "SELECT * FROM DATA_TABLE;"
            }
        env:
          type: array
          description: Environment variables and values
          items:
            type: object
            properties:
              name:
                type: string
                description: Name of environment variable
                example: "IMG_SIZE"
              value:
                type: string
                description: Value of environment variable
                example: "2.5"
    PutJobResponse:
      type: object
      properties:
        job_id:
          type: string
          description: UUID of new job
          example: "c2c5484c22a8434aa301e4f56d17d595"
    GetJob:
      type: object
      properties:
        status:
          type: string
          description: Job fetch status
          example: "ok"
        msg:
          type: string
          description: Job fetch message
          example: ""
        job:
          type: object
          description: Information about the requested job
          properties:
            clusterId:
              type: string
              description: ID of HTCondor cluster assigned
              example: abc123
            state:
              type: string
              description: State of the job
              example: running
            type:
              type: string
              description: Job type
              example: "pipeline"
            input:
              type: object
              description: Input parameter values. Schema depends on job type.
              properties:
                EXAMPLE_PARAM:
                  type: string
                  description: Example of an environment variable EXAMPLE_PARAM
                  example: "Example of an environment variable EXAMPLE_PARAM"
            output:
              type: object
              description: Job output data
              properties:
                urls:
                  type: array
                  description: URLs to output data files
                  items:
                    type: string
                    description: Output data file URL
                    example: "https://example.com/path/to/file.dat"
                data:
                  type: object
                  description: Direct output data/information. Schema depends on job type.
                  properties:
                    EXAMPLE:
                      type: string
                      description: Example parameter returned by the job
                      example: "Example value returned by the job"
################################################################################
`;