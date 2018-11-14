// gcc server.c -lfadc -lvme -lm -o server

// Libraries that should be widely available.
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <sys/wait.h>
#include <signal.h>
#include <fcntl.h>
#include <sys/select.h>
#include <sys/timex.h>
#include <ctype.h>
#include <termios.h>
#include <time.h>
#include <sys/time.h>
#include <asm/socket.h>
#include <float.h>

// VME/FADC libraries.
#include <vme/vme_api.h>
#include <fadc_lowlevel.h>  /* needed to access low-level routines */
#include <fadc.h>

/* GLOBALS */

// Server Settings
#define PORT "3491" // The port users will be connecting to.
#define BACKLOG 10 // How many pending connections queue will hold.
#define MAXDATASIZE 100 // Buffer size for receiving.

/* These are globals related to server CBLT commands, i.e. not libfadc stuff */
// Parameter get commands
#define GET_DATA_WIDTH 50
#define GET_DATA_OFFSET 51
#define GET_AREA_WIDTH 52
#define GET_AREA_OFFSET 53
#define GET_REREAD_WIDTH 54
#define GET_REREAD_OFFSET 55
#define GET_HILO_WIDTH 56
#define GET_HILO_OFFSET 57
#define GET_CFD_THRESH 58
#define GET_0_SUPRESS_LEVEL 59
#define READ_ALL_PARAMS 60
#define GET_FADC_MODE 61
#define GET_REREAD_MODE 62
#define GET_VERBOSITY 63
#define GET_TIMEIN 64

// Parameter set commands
#define SET_DATA_WIDTH 150
#define SET_DATA_OFFSET 151
#define SET_AREA_WIDTH 152
#define SET_AREA_OFFSET 153
#define SET_REREAD_WIDTH 154
#define SET_REREAD_OFFSET 155
#define SET_HILO_WIDTH 156
#define SET_HILO_OFFSET 157
#define SET_CFD_THRESH 158
#define SET_0_SUPRESS_LEVEL 159
#define CLEAR_ALL_SCALARS 160
#define SET_FADC_MODE 161
#define SET_REREAD_MODE 162
#define SET_VERBOSITY 163
#define SET_TIMEIN 164

// DACQ commands.
#define CLEAR_EVENT 200
#define SINGLE_CBLT 201
#define TIMED_CBLT 202
#define EVENT_CBLT 203
#define CONTINUOUS_CBLT 204
#define AUTOMATED_CBLT 205
#define SINGLE_REREAD 207
#define CLOSE_SERVER 255

// Verbosity and print statements.
const unsigned char VERBOSE_ON = 1;
const unsigned char VERBOSE_OFF = 0;
unsigned char verbose_status = 0;
const char *unifiedStrings[12];
const char *rereadStrings[6];
const char *blankStrings[12];

// Status and execution rendevous values.
// I used 1 for good/on/proceed and 0 for bad/off/halt.
const unsigned char SERVER_CLOSED = 0;
const unsigned char RENDEVOUS_PROCEED = 1;
const unsigned char RENDEVOUS_HALT = 0;
unsigned char client_rendevous = 255;
unsigned char server_status = 1;

// unified constraint
// TIMED = seconds
// EVENT = # of events
// CONTINUOUS = 1 (RENDEVOUS_PROCEED)
// AUTOMATED = milliseconds
unsigned int client_constraint;

// Timing variables
struct timeval START_TIME, CURRENT_TIME;
double ELAPSED_TIME;
unsigned int requested_timein = 10000;

// Reread settings.
const unsigned char REREAD_ON = 1;
const unsigned char REREAD_OFF = 0;
unsigned char reread_status = 0;

/* libfadc/hardware variables */
/* ############################## */
#define MAXLLEN         80
#define MAX_FADC_BYTES  9000
#define SIGNUM          30      /* SIGUSR1 */
#define DMA_BUFSIZE     16384   /* dma buffer size in bytes */
#define STR_LEN 1024

char Berr_flag=0;
int Boardnum=-1;
int Boardnum7 = 7;
int Boardnum8 = 8;
int Boardnum9 = 9;
int Firstboard = -1;  /* default to clock board*/
int Lastboard = 9;

int Current_mode = FULL_MODE;  /* read all 10 chans */

unsigned long *clkbd_lptr;   /* pointer for D32 CLKBD transfers    */
unsigned long *fadc_lptr;
unsigned long *fadc_lptr7;
unsigned long *fadc_lptr8;
unsigned long *fadc_lptr9;

int Boardnum;

/* ############################## */


/* FORWARD DECLARATIONS */

// Server
void acquire_network_info(struct addrinfo *pHints, struct addrinfo **ppServInfo); // Get the info to create a socket for TCP communication.
int bind_addr(struct addrinfo *serverInfo); // To bind socket.
void listen_addr(int socket); // To listen for connections.
void *get_in_addr(struct sockaddr *sa); // Get human-readable IP.
int stream_send(int comm_socket, long *pStart, int *N);
void server_closer();

int do_reread(int comm_socket_, unsigned long *dmabuffer_, const char *rereadStrings[]);
void unifiedCBLT(int comm_socket_, unsigned char command_request_, unsigned long *dmabuffer_, const char *unifiedStrings[], const char *rereadStrings[]);
void universalBoardGet(int comm_socket_, unsigned char command_request_);
void universalChannelGet(int comm_socket_, unsigned char command_request_);
void universalChannelSet(int comm_socket_, unsigned char command_request_);
void universalBoardSet(int comm_socket_, unsigned char command_request_);

// ease-of-use functions.
void print_buffer(long *buffer, int words);
void printword(unsigned long wd);
void printBits(size_t const size, void const * const ptr);
void clear_clk_scalars(void);

int main(void) {
    
    // Socket related variables.
    int binded_socket, comm_socket;  // listen on listen_socket, new connection on comm_socket
    struct addrinfo hints, *servinfo, *p; // addrinfo struct for storing network info
    struct sockaddr_storage their_addr; // connector's address information. sockaddr_storage is a general container that typecasts to sockaddr.
    socklen_t sin_size; // currently maximum bytes of addr, later the actual size (i.e possibly less).
    struct sigaction sa;
    char s[INET6_ADDRSTRLEN]; // A string to hold the IP address.

    // Communication related variables.
    int sent_nbytes, recv_nbytes;
    unsigned char command_request;

    // CBLT variables.
    int returned_nwords;

    /* libfadc/hardware variables */
    /* ############################## */
    int i, n, rv;
	int board_no;
    unsigned long *lptr;
	
    int low, high, numboards;
    unsigned long *dmabuffer;
    char filename[128], answer[10];
    /* ############################## */

    unifiedStrings[0] = "1U-S Sent Value: %d of length %d (Server Begin Rendevous.)\n";
    unifiedStrings[1] = "2U-R Received Value: %d with length %d (Constraint Send).\n";
    unifiedStrings[2] = "3U-S Sent Value: %d with length %d (CBLT Status Rendevous).\n";
    unifiedStrings[3] = "4U-R Received Value: %d with length %d (Send nwords Rendevous).\n";
    unifiedStrings[4] = "5U-S Sent Value: %d of length %d (nwords).\n";
    unifiedStrings[5] = "6U-R Received Value: %d with length %d (nwords Rendevous).\n";
    unifiedStrings[6] = "7U-S Sent Value: %d and length %d (CBLT bytes).\n";
    unifiedStrings[7] = "8U-R Received Value: %d with length %d (CBLT complete Rendevous).\n";
    unifiedStrings[8] = "9U-S Sent Value: %d of length %d (Continue Rendevous)\n";
    unifiedStrings[9] = "10U-S Sent Value: %d with length %d (OK continue Rendevous).\n";
    unifiedStrings[10] = "11U-S Sent Value: %d with length %d (1st Short circuit).\n";
    unifiedStrings[11] = "12U-S Sent Value: %d with length %d (2nd Short circuit).\n";
    unifiedStrings[12] = "13U-S Sent Value: %d with length %d (3rd Short circuit).\n";
    

    rereadStrings[0] = "1R-S Sent Value: %d with length %d (CBLT reread Status Rendevous).\n";
    rereadStrings[1] = "2R-R Received Value: %d with length %d (Send reread nwords Rendevous).\n";
    rereadStrings[2] = "3R-S Sent Value: %d with length %d (reread nwords value).\n";
    rereadStrings[3] = "4R-R Received Value: %d with length %d (Send reread CBLT Rendevous).\n";
    rereadStrings[4] = "5R-S Sent Value: %d with length %d (reread CBLT data).\n";
    rereadStrings[5] = "6R-R Received Value: %d with length %d (reread CBLT complete Rendevous).\n";

    blankStrings[0] = "";
    blankStrings[1] = "";
    blankStrings[2] = "";
    blankStrings[3] = "";
    blankStrings[4] = "";
    blankStrings[5] = "";
    blankStrings[6] = "";
    blankStrings[7] = "";
    blankStrings[8] = "";
    blankStrings[9] = "";
    blankStrings[10] = "";
    blankStrings[11] = "";
    blankStrings[12] = "";


    // To always know the machines implementation of data types.
    printf("Lets get this out of the way:\n\n char: %d bytes\n int: %d bytes\n long: %d bytes\n unsigned long long int: %d bytes\n float: %d bytes\n double: %d bytes\n \n\n", sizeof(unsigned char), sizeof(unsigned int), sizeof(unsigned long), sizeof(unsigned long long int), sizeof(float), sizeof(double));

    fadc_init();
    fadc_verbose(1);
    atexit( fadc_exit );

    low = 999;
    high = -999;
    numboards = 0;
    for (i = 0; i < fadc_num_boards(); i++) {
        if (fadc_is_board_present(i)) {
	        if (i < low) low = i;
	        if (i >= high) high = i;
	        numboards++;
	    }
    }

    if (Boardnum == -1) Boardnum = low;

    if (numboards <= 1) {
	    Firstboard = -1;
	    Lastboard = Boardnum;
    }
    else {
	    Firstboard = low;
	    Lastboard = high;
    }

    dmabuffer = fadc_alloc_cblt_buffer(DMA_BUFSIZE, Firstboard, Lastboard);
    if (dmabuffer == NULL) {
        printf("Couldn't allocate memory for CBLT transfer\n");
        exit(1);
    }
    printf( "CBLT: Firstboard=%d, Lastboard=%d\n", Firstboard, Lastboard);

    /* load board settings */
    fadc_verbose(0);
    for (i = 0; i < fadc_num_boards(); i++){
      if ( fadc_is_board_present(i) ) {
		sprintf( filename, "fadc-board-%d.settings", i );
		printf("Loading settings for board in slot %d...\n", i);
		if (fadc_load_settings( i, filename )) {
			printf("\n** No settings file was detected for board %d\n", i);
			printf("** You should run 'testfadc -b %d', set up the\n", i);
			printf("** board and save its settings file.\n");
			printf("** Do you want to continue with the defaults? (y/n) ");
			scanf("%s", answer);
			if( tolower(answer[0]) != 'y') {
				exit(0);
			}
		}
      }
    }
    fadc_verbose(1);


    /* Set some pointers to the boards for low-level access */

    clkbd_lptr = fadc_get_clk_lptr();
    fadc_lptr = fadc_get_fadc_lptr(Boardnum);
	fadc_lptr7 = fadc_get_fadc_lptr(Boardnum7);
	fadc_lptr8 = fadc_get_fadc_lptr(Boardnum8);
    fadc_lptr9 = fadc_get_fadc_lptr(Boardnum9);

    printf("lptr addr for FADC bd %d = 0x%08lx\n", Boardnum,
	   (unsigned long) fadc_lptr);	
    printf("lptr addr for FADC bd %d = 0x%08lx\n", Boardnum7,
	   (unsigned long) fadc_lptr7);
    printf("lptr addr for FADC bd %d = 0x%08lx\n", Boardnum8,
	   (unsigned long) fadc_lptr8);
    printf("lptr addr for FADC bd %d = 0x%08lx\n", Boardnum9,
	   (unsigned long) fadc_lptr9);
    printf("lptr addr for CLK bd = 0x%08lx\n", (unsigned long) clkbd_lptr);


    /* Set event number and clear out event */

    fadc_set_mode(Boardnum7, WORD_MODE);	     
    wr_evt_no(fadc_lptr7, 0xac000000); 
    fadc_set_mode(Boardnum8, WORD_MODE);	     
    wr_evt_no(fadc_lptr8, 0xac000000); 
    fadc_set_mode(Boardnum9, WORD_MODE);	     
    wr_evt_no(fadc_lptr9, 0xac000000); 
    fadc_set_mode( Boardnum7, Current_mode );
    fadc_set_mode( Boardnum8, Current_mode );
    fadc_set_mode( Boardnum9, Current_mode );	
    fadc_evt_clr();

    acquire_network_info(&hints, &servinfo); // Modifies servinfo to point to system address info.

    binded_socket = bind_addr(servinfo); // Wrapper for bind with error-checking. Returns the socket we will listen on.
    listen_addr(binded_socket); // Listen for incoming connections.

    // Accept the incoming connection on the listen socket. Returns the new port we actually communicate over.
    // their_addr is filled out with the incoming connection's info.
    // This blocks until acceptance.
    printf("Server: waiting for connections...\n");
    sin_size = sizeof(their_addr);
    comm_socket = accept(binded_socket, (struct sockaddr *)&their_addr, &sin_size);

    if (comm_socket == -1) {
        perror("accept");
    }

    // Get the the human-readable IP4/6 address and put in s. 
    inet_ntop(their_addr.ss_family, get_in_addr((struct sockaddr *)&their_addr), s, sizeof(s));
    printf("Server: got connection from %s\n", s);


    printf("Entering while loop.\n\n");
    while (server_status != SERVER_CLOSED) {

        // Command request.
        printf("Server status: %d\n", server_status);
        printf("Waiting for command...\n");
        command_request = 0;
        recv_nbytes = recv(comm_socket, &command_request, 1, 0);
        printf("1C-R Received Value: %d with length %d (Command Request).\n", command_request, recv_nbytes);
        fflush(stdout);

        // Switch statement for parsing commands.
        switch (command_request) {
            case CLOSE_SERVER:
                server_status = 0;
                //server_closer();
                printf("Got server close request. Closing...\n");
                sent_nbytes = send(comm_socket, &SERVER_CLOSED, 1, 0);
                break;

            case CLEAR_EVENT:
                printf("Got event clear request...");
                fadc_evt_clr();
                printf("cleared.\n");
                break;

            case SINGLE_CBLT:

                rv = timein_event(requested_timein);

                if (rv != 1) {
                    sent_nbytes = send(comm_socket, &RENDEVOUS_HALT, 1, 0); //Short circuits 1N-S
                    printf("No initial event; capture timed-out. Returning.\n");
                    break;
                }

                returned_nwords = fadc_cblt();

                if ( returned_nwords > 0 ) {
                    sent_nbytes = send(comm_socket, &RENDEVOUS_PROCEED, 1, 0);
                    printf("", RENDEVOUS_PROCEED, sent_nbytes);
                    //printf("1N-S Sent Value: %d with length %d (CBLT Status Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes);
                } else {
                    sent_nbytes = send(comm_socket, &RENDEVOUS_HALT, 1, 0);
                    printf("1N-S Sent Value: %d with length %d (CBLT Status Rendevous).\n", RENDEVOUS_HALT, sent_nbytes);
                    printf("Got bad value for returned_nwords: %d . Breaking.\n", returned_nwords);
                    break;
                }

                recv_nbytes = recv(comm_socket, &client_rendevous, 1, 0);
                printf("2N-R Received Value: %d with length %d (Send nwords Rendevous).\n", client_rendevous, recv_nbytes);

                if (client_rendevous = RENDEVOUS_PROCEED) {
                    client_rendevous = 255;
                    sent_nbytes = send(comm_socket, &returned_nwords, sizeof(int), 0);
                    printf("3N-S Sent Value: %d with length %d (nwords value).\n", returned_nwords, sent_nbytes);
                } else {
                    client_rendevous = 255;
                    printf("Got bad rendevous from client. Breaking.\n");
                    break;
                }

                recv_nbytes = recv(comm_socket, &client_rendevous, 1, 0);
                printf("4N-R Received Value: %d with length %d (Send CBLT Rendevous).\n", client_rendevous, recv_nbytes);

                if (client_rendevous == RENDEVOUS_PROCEED) {
                    client_rendevous = 255;
                    int numbytes = sizeof(long)*returned_nwords;
                    sent_nbytes = stream_send(comm_socket, dmabuffer, &numbytes);
                    printf("5N-S Sent Value: %d with length %d (CBLT data).\n", numbytes, sent_nbytes);
                } else {
                    client_rendevous = 255;
                    printf("Got bad rendevous from client. Breaking.\n");
                    break;                    
                }

                recv_nbytes = recv(comm_socket, &client_rendevous, 1, 0);
                printf("6N-R Received Value: %d with length %d (CBLT complete Rendevous).\n", client_rendevous, recv_nbytes);

                if (client_rendevous != RENDEVOUS_PROCEED) {
                    printf("Got bad Rendevous. Breaking.\n");
                    break;
                }
                client_rendevous = 255;

                if ( reread_status == REREAD_ON ) {
                    rv = do_reread(comm_socket, dmabuffer, rereadStrings);
                }

                if (rv != 1) {
                    break;
                }

                fadc_evt_clr();
                returned_nwords = 0;
                fflush(stdout);              
                break;

            case TIMED_CBLT:
                if (verbose_status == 1) {
                    unifiedCBLT(comm_socket, command_request, dmabuffer, unifiedStrings, rereadStrings);
                    break;
                } else {
                    unifiedCBLT(comm_socket, command_request, dmabuffer, blankStrings, blankStrings);
                    break;                    
                }

            case EVENT_CBLT:
                if (verbose_status == 1) {
                    unifiedCBLT(comm_socket, command_request, dmabuffer, unifiedStrings, rereadStrings);
                    break;
                } else {
                    unifiedCBLT(comm_socket, command_request, dmabuffer, blankStrings, blankStrings);
                    break;                    
                }
            case CONTINUOUS_CBLT:
                if (verbose_status == 1) {
                    unifiedCBLT(comm_socket, command_request, dmabuffer, unifiedStrings, rereadStrings);
                    break;
                } else {
                    unifiedCBLT(comm_socket, command_request, dmabuffer, blankStrings, blankStrings);
                    break;                    
                }
            case AUTOMATED_CBLT:
                if (verbose_status == 1) {
                    unifiedCBLT(comm_socket, command_request, dmabuffer, unifiedStrings, rereadStrings);
                    break;
                } else {
                    unifiedCBLT(comm_socket, command_request, dmabuffer, blankStrings, blankStrings);
                    break;                    
                }

            //Getters
            case GET_DATA_WIDTH:
                universalBoardGet(comm_socket, command_request);         
                break;
            case GET_DATA_OFFSET:
                universalChannelGet(comm_socket, command_request);         
                break;
            case GET_AREA_WIDTH:
                universalChannelGet(comm_socket, command_request);         
                break;
            case GET_AREA_OFFSET:
                universalChannelGet(comm_socket, command_request);         
                break;
            case GET_REREAD_WIDTH:
                universalBoardGet(comm_socket, command_request);
                break;
            case GET_REREAD_OFFSET:
                universalChannelGet(comm_socket, command_request);         
                break;
            case GET_HILO_WIDTH:
                universalBoardGet(comm_socket, command_request);
                break;
            case GET_HILO_OFFSET:
                universalChannelGet(comm_socket, command_request);         
                break;
            case GET_CFD_THRESH:
                universalChannelGet(comm_socket, command_request);         
                break;
            case GET_0_SUPRESS_LEVEL:
                universalChannelGet(comm_socket, command_request);         
                break;
            case READ_ALL_PARAMS:
                break;
            case GET_FADC_MODE:
                break;
            case GET_REREAD_MODE:
                sent_nbytes = send(comm_socket, &reread_status, 1, 0);
                printf("1S-S Sent Value: %d with length %d (Send status Rendevous).\n", reread_status, sent_nbytes);
                break;
            case GET_VERBOSITY:
                sent_nbytes = send(comm_socket, &verbose_status, 1, 0);
                printf("1S-S Sent Value: %d with length %d (Send status Rendevous).\n", verbose_status, sent_nbytes);
                break;
            case GET_TIMEIN:
                sent_nbytes = send(comm_socket, &requested_timein, 4, 0);
                printf("1S-S Sent Value: %d with length %d (Send status Rendevous).\n", requested_timein, sent_nbytes);
                break;                              

        // Parameter set commands
            case SET_DATA_WIDTH:
                universalBoardSet(comm_socket, command_request);
                break;
            case SET_DATA_OFFSET:
                universalChannelSet(comm_socket, command_request);
                break;
            case SET_AREA_WIDTH:
                universalChannelSet(comm_socket, command_request);
                break;
            case SET_AREA_OFFSET:
                universalChannelSet(comm_socket, command_request);
                break;
            case SET_REREAD_WIDTH:
                universalBoardSet(comm_socket, command_request);
                break;
            case SET_REREAD_OFFSET:
                universalChannelSet(comm_socket, command_request);
                break; 
            case SET_HILO_WIDTH:
                universalBoardSet(comm_socket, command_request);
                break;
            case SET_HILO_OFFSET:
                universalChannelSet(comm_socket, command_request);
                break; 
            case SET_CFD_THRESH:
                universalChannelSet(comm_socket, command_request);
                break;
            case SET_0_SUPRESS_LEVEL:
                universalChannelSet(comm_socket, command_request);
                break; 
            case CLEAR_ALL_SCALARS:
            case SET_FADC_MODE:
            case SET_REREAD_MODE:

                sent_nbytes = send(comm_socket, &RENDEVOUS_PROCEED, 1, 0);
                printf("1S-S Sent Value: %d with length %d (Send status Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes);                

                recv_nbytes = recv(comm_socket, &reread_status, 1, 0);
                printf("2S-R Received Value: %d with length %d (Reread status).\n", reread_status, recv_nbytes);

                break;

            case SET_VERBOSITY:

                sent_nbytes = send(comm_socket, &RENDEVOUS_PROCEED, 1, 0);
                printf("1S-S Sent Value: %d with length %d (Send status Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes);                

                recv_nbytes = recv(comm_socket, &verbose_status, 1, 0);
                printf("2S-R Received Value: %d with length %d (Verbosity status).\n", verbose_status, recv_nbytes);

                break;

            case SET_TIMEIN:

                sent_nbytes = send(comm_socket, &RENDEVOUS_PROCEED, 1, 0);
                printf("1S-S Sent Value: %d with length %d (Send status Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes);                

                recv_nbytes = recv(comm_socket, &requested_timein, 4, 0);
                printf("2S-R Received Value: %d with length %d (Verbosity status).\n", requested_timein, recv_nbytes);                

                break;

            default:
                printf("Unkown command or something else wrong: %d . \n", command_request);
                break;

        }

    }

    freeaddrinfo(servinfo); // Destroy a addrinfo structure.
    close(binded_socket);

    return 0;
}

void universalBoardGet(int comm_socket_, unsigned char command_request_) {
    int sent_nbytes_, recv_nbytes_, board_no_;
    unsigned char client_rendevous_ = 255;
    unsigned long current_parameter;

    for (board_no_ = Boardnum7; board_no_ <= Boardnum9; board_no_++) {

        fadc_set_mode(board_no_, WORD_MODE);

        switch (command_request_) {
            case GET_DATA_WIDTH:
                printf("Data Width Request.\n");
                current_parameter = fadc_get_data_width(board_no_);
                break;
            case GET_REREAD_WIDTH:
                printf("Reread Width Request\n");
                current_parameter = fadc_get_reread_width(board_no_);
                break;
            case GET_HILO_WIDTH:
                printf("HILO Width Request\n");
                current_parameter = fadc_get_hilo_width(board_no_);
                break;
        }

        if (current_parameter >= 0) {
            sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
            printf("1G-S Sent Value: %d with %d bytes (Getter OK Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes_);
        } else {
            sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
            printf("1G-S Sent Value: %d with %d bytes (Getter OK Rendevous).\n", RENDEVOUS_HALT, sent_nbytes_);
            printf("Breaking...");
            break;
        }

        recv_nbytes_ = recv(comm_socket_, &client_rendevous_, 1, 0);
        printf("2G-R Received Value: %d with %d bytes (Send Value Rendevous).\n", client_rendevous_, recv_nbytes_);

        if (client_rendevous_ == 1) {
            client_rendevous_ = 255;
            sent_nbytes_ = send(comm_socket_, &current_parameter, sizeof(long), 0);
            printf("3G-S Sent Value: %d with %d bytes (Parameter Send).\n", current_parameter, sent_nbytes_);
        } else {
            printf("Got Bad Rendevous. Breaking.");
            break;
        }

        recv_nbytes_ = recv(comm_socket_, &client_rendevous_, 1, 0);
        printf("4G-R Received Value: %d with %d bytes (Got Parameter Rendevous).\n", client_rendevous_, recv_nbytes_);                    
        if (client_rendevous_ != 1) {
            printf("Got Bad Rendevous. Breaking.");
            break;                        
        }
        client_rendevous_ = 255;

        if (board_no_ == Boardnum9) {
            sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
            printf("5G-S Sent Value: %d with %d bytes (Continue Rendevous).\n", RENDEVOUS_HALT, sent_nbytes_);
        } else {
            sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
            printf("5G-S Sent Value: %d with %d bytes (Continue Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes_);                        
        }
        fadc_set_mode(board_no_, Current_mode);
    }
    fflush(stdout);

}

void universalChannelGet(int comm_socket_, unsigned char command_request_) {
    int sent_nbytes_, recv_nbytes_, board_no_, i_;
    unsigned char client_rendevous_ = 255;
    unsigned long current_parameter; 

    for (board_no_ = Boardnum7; board_no_ <= Boardnum9; board_no_++) {
        fadc_set_mode(board_no_, WORD_MODE);
        for (i_ = 0; i_ < 10; i_++) {
            switch (command_request_) {
                case GET_DATA_OFFSET:
                    current_parameter = fadc_get_data_offset(board_no_, i_);
                    break;
                case GET_AREA_WIDTH:
                    current_parameter = fadc_get_area_width(board_no_, i_);
                    break;
                case GET_AREA_OFFSET:
                    current_parameter = fadc_get_area_offset(board_no_, i_);
                    break;
                case GET_REREAD_OFFSET:
                    current_parameter = fadc_get_reread_offset(board_no_, i_);
                    break;
                case GET_HILO_OFFSET:
                    current_parameter = fadc_get_hilo_offset(board_no_, i_);
                    break;
                case GET_CFD_THRESH:
                    current_parameter = fadc_get_cfd_thresh(board_no_, i_);
                    break;
                case GET_0_SUPRESS_LEVEL:
                    current_parameter = fadc_get_area_discrim(board_no_, i_);
                    break;
            }

            if (current_parameter >= 0) {
                sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
                printf("1G-S Sent Value: %d with %d bytes (Getter OK Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes_);
            } else {
                sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
                printf("1G-S Sent Value: %d with %d bytes (Getter OK Rendevous).\n", RENDEVOUS_HALT, sent_nbytes_);
                printf("Breaking...");
                break;
            }

            recv_nbytes_ = recv(comm_socket_, &client_rendevous_, 1, 0);
            printf("2G-R Received Value: %d with %d bytes (Send Value Rendevous).\n", client_rendevous_, recv_nbytes_);

            if (client_rendevous_ == 1) {
                client_rendevous_ = 255;
                sent_nbytes_ = send(comm_socket_, &current_parameter, sizeof(long), 0);
                printf("3G-S Sent Value: %d with %d bytes (Parameter Send).\n", current_parameter, sent_nbytes_);
            } else {
                printf("Got Bad Rendevous. Breaking.");
                break;
            }

            recv_nbytes_ = recv(comm_socket_, &client_rendevous_, 1, 0);
            printf("4G-R Received Value: %d with %d bytes (Got Parameter Rendevous).\n", client_rendevous_, recv_nbytes_);                    
            if (client_rendevous_ != 1) {
                printf("Got Bad Rendevous. Breaking.");
                break;                        
            }
            client_rendevous_ = 255;

            if (board_no_ == Boardnum9 && i_ == 9) {
                sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
                printf("5G-S Sent Value: %d with %d bytes (Continue Rendevous).\n", RENDEVOUS_HALT, sent_nbytes_);
            } else {
                sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
                printf("5G-S Sent Value: %d with %d bytes (Continue Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes_);                        
            }
        }
        fadc_set_mode(board_no_, Current_mode);

    }
    fflush(stdout);
}


void universalBoardSet(int comm_socket_, unsigned char command_request_) {
    int sent_nbytes_, recv_nbytes_, board_no_;
    unsigned long i_, boards_, value_;
    unsigned long bit_mask_ = 1;
    unsigned long current_parameter;

    sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
    printf("1S-S Sent Value: %d with %d bytes (Setter OK Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes_);

    recv_nbytes_ = recv(comm_socket_, &boards_, sizeof(unsigned long), 0);
    printf("2S-R Received Value: %d with %d bytes (Send channels).\n", boards_, recv_nbytes_);
    printBits(sizeof(boards_), &boards_);

    sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
    printf("3S-S Sent Value: %d with %d bytes (Boards OK Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes_);

    recv_nbytes_ = recv(comm_socket_, &value_, sizeof(unsigned long), 0);
    printf("4S-R Received Value: %d with %d bytes (Send Value).\n", value_, recv_nbytes_); 

    i_ = 0;
    for (board_no_ = Boardnum7; board_no_ <= Boardnum9; board_no_++) {
        fadc_set_mode(board_no_, WORD_MODE);
        printf("Bit Mask Result: %lu\n", ((boards_ >> i_) & bit_mask_));
        if ( ((boards_ >> i_) & bit_mask_) == 1 ) {
            switch (command_request_) {
                case SET_DATA_WIDTH:
                    fadc_set_data_width(board_no_, value_);
                    current_parameter = fadc_get_data_width(board_no_);
                    printf("DATA WIDTH: \n BOARD: %lu \n SET VALUE: %lu \n ACTUAL VALUE: %lu\n", board_no_, value_, current_parameter);
                    break;
                case SET_REREAD_WIDTH:
                    fadc_set_reread_width(board_no_, value_);
                    current_parameter = fadc_get_reread_width(board_no_);
                    printf("DATA WIDTH: \n BOARD: %lu \n SET VALUE: %lu \n ACTUAL VALUE: %lu\n", board_no_, value_, current_parameter);
                    break;
                case SET_HILO_WIDTH:
                    fadc_set_hilo_width(board_no_, value_);
                    current_parameter = fadc_get_hilo_width(board_no_);
                    printf("DATA WIDTH: \n BOARD: %lu \n SET VALUE: %lu \n ACTUAL VALUE: %lu\n", board_no_, value_, current_parameter);
                    break;
                default:
                    break;
            }
        }
        fadc_set_mode(board_no_, Current_mode);
        i_++;
    }
    sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
    printf("5S-R Sent Value: %d with %d bytes (Setter Complete Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes_);
}


void universalChannelSet(int comm_socket_, unsigned char command_request_) {
    int sent_nbytes_, recv_nbytes_, board_no_;
    unsigned long i_, channels_, value_;
    unsigned long bit_mask_ = 1;

    sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
    printf("1S-S Sent Value: %d with %d bytes (Setter OK Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes_);

    recv_nbytes_ = recv(comm_socket_, &channels_, sizeof(unsigned long), 0);
    printf("2S-R Received Value: %d with %d bytes (Send channels).\n", channels_, recv_nbytes_);
    printBits(sizeof(channels_), &channels_);

    sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
    printf("3S-S Sent Value: %d with %d bytes (Channels OK Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes_);

    recv_nbytes_ = recv(comm_socket_, &value_, sizeof(unsigned long), 0);
    printf("4S-R Received Value: %d with %d bytes (Send Value).\n", value_, recv_nbytes_);    

    for (board_no_ = Boardnum7; board_no_ <= Boardnum9; board_no_++) {
        fadc_set_mode(board_no_, WORD_MODE);

        for (i_ = 0; i_ < 10; i_++) {
            printf("Bit Mask Result: %lu\n", ((channels_ >> i_) & bit_mask_));
            if ( ((channels_ >> i_) & bit_mask_) == 1 ) {
                printf("Digit %lu is changed.\n", i_);
                switch (command_request_) {
                    case SET_DATA_OFFSET:
                        fadc_set_data_offset(board_no_, i_, value_);
                        break;
                    case SET_AREA_WIDTH:
                        fadc_set_area_width(board_no_, i_, value_);
                        break;
                    case SET_AREA_OFFSET:
                        fadc_set_area_offset(board_no_, i_, value_);
                        break;
                    case SET_REREAD_OFFSET:
                        fadc_set_reread_offset(board_no_, i_, value_);
                        break;
                    case SET_HILO_OFFSET:
                        fadc_set_hilo_offset(board_no_, i_, value_);
                        break;
                    case SET_CFD_THRESH:
                        fadc_set_cfd_thresh(board_no_, i_, value_);
                        break;
                    case SET_0_SUPRESS_LEVEL:
                        fadc_set_area_discrim(board_no_, i_, value_);
                        break;
                }
            }
        }
        fadc_set_mode(board_no_, Current_mode);
        channels_ = channels_ >> 10;      
    }
    sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
    printf("5S-R Sent Value: %d with %d bytes (Setter Complete Rendevous).\n", RENDEVOUS_PROCEED, sent_nbytes_);
}


int do_reread(int comm_socket_, unsigned long *dmabuffer_, const char *rereadStrings[]) {

    int sent_nbytes_, recv_nbytes_, rv;
    unsigned long returned_nwords_;

    fadc_request_reread();
    
    rv = timein_event(requested_timein);

    if (rv != 1) {
        sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0); //Short circuits 1R-S
        printf("No initial event; capture timed-out. Returning.\n");
        return 0;
    }

    returned_nwords_ = fadc_cblt();

    if ( returned_nwords_ > 0 ) {
        sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
        printf(rereadStrings[0], RENDEVOUS_PROCEED, sent_nbytes_);
    } else {
        sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
        printf(rereadStrings[0], RENDEVOUS_HALT, sent_nbytes_);
        printf("Got bad value for returned_nwords: %d . Breaking.\n", returned_nwords_);
        return 0;
    }

    recv_nbytes_ = recv(comm_socket_, &client_rendevous, 1, 0);
    printf(rereadStrings[1], client_rendevous, recv_nbytes_);

    if (client_rendevous = RENDEVOUS_PROCEED) {
        client_rendevous = 255;
        sent_nbytes_ = send(comm_socket_, &returned_nwords_, sizeof(int), 0);
        printf(rereadStrings[2], returned_nwords_, sent_nbytes_);
    } else {
        client_rendevous = 255;
        printf("Got bad rendevous from client. Breaking.\n");
        return 0;
    }

    recv_nbytes_ = recv(comm_socket_, &client_rendevous, 1, 0);
    printf(rereadStrings[3], client_rendevous, recv_nbytes_);

    if (client_rendevous == RENDEVOUS_PROCEED) {
        client_rendevous = 255;
        int numbytes = sizeof(long)*returned_nwords_;
        sent_nbytes_ = stream_send(comm_socket_, dmabuffer_, &numbytes);
        printf(rereadStrings[4], numbytes, sent_nbytes_);
    } else {
        client_rendevous = 255;
        printf("Got bad rendevous from client. Breaking.\n");
        return 0;                    
    }

    recv_nbytes_ = recv(comm_socket_, &client_rendevous, 1, 0);
    printf(rereadStrings[5], client_rendevous, recv_nbytes_);
    client_rendevous = 255;

    return 1;
}

int timein_event(int max_ms_) {
    gettimeofday(&START_TIME, NULL);
    while (fadc_got_event() == 0) {
        gettimeofday(&CURRENT_TIME, NULL);
        ELAPSED_TIME = (CURRENT_TIME.tv_sec - START_TIME.tv_sec) * 1000.0;
        ELAPSED_TIME += (CURRENT_TIME.tv_usec - START_TIME.tv_usec) / 1000.0;
        if (ELAPSED_TIME > max_ms_) {
            return 0;
        }
    }
    return 1;
}


void unifiedCBLT(int comm_socket_, unsigned char command_request_, unsigned long *dmabuffer_, const char *unifiedStrings[], const char *rereadStrings[]) {


    int sent_nbytes_, recv_nbytes_, returned_nwords_;
    int rv;
    unsigned int n = 0;
    double end_value, current_value, remaining_value;

    sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
    printf(unifiedStrings[0], RENDEVOUS_PROCEED, sent_nbytes_);

    recv_nbytes_ = recv(comm_socket_, &client_constraint, sizeof(unsigned int), 0);
    printf(unifiedStrings[1], client_constraint, recv_nbytes_);
    printf("client_constraint: %d\n", client_constraint);

    if (command_request_ == TIMED_CBLT) {
        end_value = client_constraint * 1000.0;
    } else if (command_request_ == EVENT_CBLT) {
        end_value = client_constraint;
    } else if (command_request_ == CONTINUOUS_CBLT) {
        end_value = 1;
    } else if (command_request_ == AUTOMATED_CBLT) {
        printf("pcommand_request_: %d\n", command_request_);
        printf("pend_value: %f\n", end_value);
        printf("pclient_constraint: %d\n", client_constraint);
        end_value = (double) client_constraint;
        printf("acommand_request_: %d\n", command_request_);
        printf("aend_value: %f\n", end_value);
        printf("aend_value: %d\n", end_value);
        printf("aclient_constraint: %d\n", client_constraint);
    } else {
        sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
        printf("Got bad command request. You should never see this happen. Returning.\n");
        return;
    }

    current_value = 0;
    remaining_value = end_value;

    rv = timein_event(requested_timein);
    if (rv != 1) {
        sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
        printf("No initial event; capture timed-out. Returning.\n");
        return;
    }

    gettimeofday(&START_TIME, NULL);
    fadc_evt_clr();
    clear_clk_scalars();

    while( current_value <= end_value) {
        //printf("end_value loop: %f\n", end_value);
        if (fadc_got_event()) {
            returned_nwords_ = fadc_cblt();

            if ( returned_nwords_ > 0 ) {
                sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
                printf(unifiedStrings[2], RENDEVOUS_PROCEED, sent_nbytes_);
            } else {
                sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
                printf(unifiedStrings[2], RENDEVOUS_HALT, sent_nbytes_);
                printf("Got bad value for returned_nwords: %d . Returning.\n", returned_nwords_);
                break;
            }

            recv_nbytes_ = recv(comm_socket_, &client_rendevous, 1, 0);
            printf(unifiedStrings[3], client_rendevous, recv_nbytes_);

            if (client_rendevous = RENDEVOUS_PROCEED) {
                client_rendevous = 255;
                sent_nbytes_ = send(comm_socket_, &returned_nwords_, sizeof(int), 0);
                printf(unifiedStrings[4], returned_nwords_, sent_nbytes_);
            } else {
                client_rendevous = 255;
                printf("Got bad rendevous from client. Returning.\n");
                break;
            }

            recv_nbytes_ = recv(comm_socket_, &client_rendevous, 1, 0);
            printf(unifiedStrings[5], client_rendevous, recv_nbytes_);

            if (client_rendevous == RENDEVOUS_PROCEED) {
                client_rendevous = 255;
                int numbytes = sizeof(long)*returned_nwords_;
                sent_nbytes_ = stream_send(comm_socket_, dmabuffer_, &numbytes);
                printf(unifiedStrings[6], numbytes, sent_nbytes_);
            } else {
                client_rendevous = 255;
                printf("Got bad rendevous from client. Returning.\n");
                break;               
            }

            recv_nbytes_ = recv(comm_socket_, &client_rendevous, 1, 0);
            printf(unifiedStrings[7], client_rendevous, recv_nbytes_);

            if (client_rendevous != RENDEVOUS_PROCEED) {
                printf("Got bad Rendevous. Returning.\n");
                break;
            }
            client_rendevous = 255;

            if ( reread_status == REREAD_ON ) {
                rv = do_reread(comm_socket_, dmabuffer_, rereadStrings);
                if (rv != 1) {
                    break;
                }
            }

            // update current value
            n += 1;
            fadc_evt_clr();
            if (command_request_ == TIMED_CBLT) {
                gettimeofday(&CURRENT_TIME, NULL);
                current_value = (CURRENT_TIME.tv_sec - START_TIME.tv_sec) * 1000.0;
                current_value += (CURRENT_TIME.tv_usec - START_TIME.tv_usec) / 1000.0;
                remaining_value = end_value - current_value;
                //printf("%f ms have passed. There are %f ms left.\n", current_value, remaining_value);
            } else if (command_request_ == EVENT_CBLT) {
                current_value = n;
                remaining_value = end_value - current_value;
                printf("%d events done. There are %d events left.\n", (int) current_value, (int) remaining_value); 
                if (current_value == end_value) {
                    sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
                    printf(unifiedStrings[10], RENDEVOUS_HALT, sent_nbytes_);

                    recv_nbytes_ = recv(comm_socket_, &client_rendevous, 1, 0);
                    printf(unifiedStrings[11], client_rendevous, recv_nbytes_);                    
                    break;
                }          
            } else if (command_request_ == CONTINUOUS_CBLT) {
                ;
            } else if (command_request_ == AUTOMATED_CBLT) {
                current_value = 0;
                gettimeofday(&START_TIME, NULL);
                while (fadc_got_event() == 0) {
                    gettimeofday(&CURRENT_TIME, NULL);
                    current_value = (CURRENT_TIME.tv_sec - START_TIME.tv_sec) * 1000.0;
                    current_value += (CURRENT_TIME.tv_usec - START_TIME.tv_usec) / 1000.0;
                    if (current_value >= end_value) {
                        break;
                    }
                }
                // printf("%f ms passed until new event.\n", current_value);                
            }

            if ( current_value <= end_value ) {
                sent_nbytes_ = send(comm_socket_, &RENDEVOUS_PROCEED, 1, 0);
                printf(unifiedStrings[8], RENDEVOUS_PROCEED, sent_nbytes_);
            } else {
                sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
                printf(unifiedStrings[8], RENDEVOUS_HALT, sent_nbytes_);                        
            }

            recv_nbytes_ = recv(comm_socket_, &client_rendevous, 1, 0);
            printf(unifiedStrings[9], client_rendevous, recv_nbytes_);
            if (client_rendevous != RENDEVOUS_PROCEED) {
                printf("Got bad Rendevous. Returning.\n");
                break;
            }
            client_rendevous = 255;



        } else {

            if (command_request_ == TIMED_CBLT) {
                //printf("%f ", current_value);
                gettimeofday(&CURRENT_TIME, NULL);
                current_value = (CURRENT_TIME.tv_sec - START_TIME.tv_sec) * 1000.0;
                current_value += (CURRENT_TIME.tv_usec - START_TIME.tv_usec) / 1000.0;
                //printf("%f ", current_value);
                if ( current_value >= end_value ) {
                    printf("Whoa there\n");
                    current_value = DBL_MAX;
                    sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
                    printf(unifiedStrings[10], RENDEVOUS_HALT, sent_nbytes_);
                    printf("(Short-circuited)\n"); // sends 3U-S's message.
                    break;
                }
            } else if (command_request_ == EVENT_CBLT) {
                current_value = n;           
            } else if (command_request_ == CONTINUOUS_CBLT) {
                ;
            } else if (command_request_ == AUTOMATED_CBLT) {
                current_value = 0;
                gettimeofday(&START_TIME, NULL);
                while (fadc_got_event() == 0) {
                    gettimeofday(&CURRENT_TIME, NULL);
                    current_value = (CURRENT_TIME.tv_sec - START_TIME.tv_sec) * 1000.0;
                    current_value += (CURRENT_TIME.tv_usec - START_TIME.tv_usec) / 1000.0;
                    if (current_value >= end_value) {
                        break;
                    }
                }
                if ( current_value >= end_value ) {
                    printf("End value: %f\n", end_value);
                    printf("Current value: %f\n", current_value);
                    sent_nbytes_ = send(comm_socket_, &RENDEVOUS_HALT, 1, 0);
                    printf(unifiedStrings[11], RENDEVOUS_HALT, sent_nbytes_);
                }
            }
        }
    }

    printf("The last value of of current_value was: %f\n", current_value);
    printf("The last value of of end_value was: %f\n", end_value);
    printf("%d events transfered.\n", n);
    fflush(stdout);              
    client_rendevous = 255;

}


void clear_clk_scalars(void) {
    unsigned long *lptr;
    
	lptr = clkbd_lptr + WR_CLK_CLR_SCALERS;
    *lptr = 0;

}

// This is mostly a convience/error-checking function.
// The return is a linked list of structs that define the socketable addresses.
// pHints: defines the criteria for what elements are returned. I have it set forIP4/IP6 agnostic and TCP communication.
// ppServInfo: is the returned linked list.
void acquire_network_info(struct addrinfo *pHints, struct addrinfo **ppServInfo) {

    int addrinfo_rv; // Return value.

    memset(pHints, 0, sizeof(*pHints)); // Set everthing to zero to be safe.
    pHints->ai_family = AF_UNSPEC; // Can be INET4 or 6.
    pHints->ai_socktype = SOCK_STREAM; // TCP
    pHints->ai_flags = AI_PASSIVE; // Address info suitable for server socket.

    addrinfo_rv = getaddrinfo(NULL, PORT, pHints, ppServInfo); // Actual call.

    // Error-checking.
    if ( addrinfo_rv != 0 ) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(addrinfo_rv));
        exit(1);
    }
}




// This function is given the server info pointer filled out by acquire_network_info.
// It returns the the binded socket.
// The bind happens on the first valid addrinfo struct. May need to make stricter.
int bind_addr(struct addrinfo *serverInfo) {

    struct addrinfo *p; // A copy for our error checking loop.
    int bind_socket; // The socket we will bind to.
    int yes = 1; //option for setsockopt.

    // loop through all the servinfo linked list elements and bind to the first we can.
    for(p = serverInfo; p != NULL; p = p->ai_next) {

        bind_socket = socket(p->ai_family, p->ai_socktype, p->ai_protocol); // Can we create the socket?
        if ((bind_socket) == -1) {
            perror("server: socket");
            continue;
        }

        // This allows the port to be reused and stop "Address already in use." errors.
        int test = setsockopt(bind_socket, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int));
        //printf("%d");
        if ( test == -1) {
            perror("setsockopt");
            exit(1);
        }

        int result = setsockopt(bind_socket, IPPROTO_TCP, TCP_NODELAY, &yes, sizeof(int));

        if (test < 0)

        if ( test == -1) {
            perror("setsockopt");
            exit(1);
        }

        //int err = setsockopt(bind_socket, SOL_SOCKET, SO_TIMESTAMPNS, &yes, sizeof(yes));

        // Try to actually bind now.
        int bind_status = bind(bind_socket, p->ai_addr, p->ai_addrlen);
        if ( bind_status == -1) {
            close(bind_socket);
            perror("Server: Failed to bind.\n");
            continue;
        }

        break; // Exit as soon as we get a valid bind.
    }

    // If something REALLY went wrong.
    if (p == NULL)  {
        fprintf(stderr, "Server: Failed to bind. Didn't have elements in linked list. \n");
        exit(1);
    }

    return bind_socket;

}


// Listen on a socket with error-checking.
void listen_addr(int socket) {

    int listen_status = listen(socket, BACKLOG); //BACKLOG defines how many conenctions can queue.

    if ( listen_status == -1) {
        perror("Server: Failed to listen.");
        exit(1);
    }

}


// Return binary IP.
void *get_in_addr(struct sockaddr *sa) {
    if (sa->sa_family == AF_INET) {
        return &(((struct sockaddr_in*)sa)->sin_addr);
    }

    return &(((struct sockaddr_in6*)sa)->sin6_addr);
}


// Transfer data over multiple packets.
int stream_send(int comm_socket, long *pStart, int *N) {

   // printf("-Preparing to send %d bytes. \n", *N);
    int sent = 0;        // Bytes sent so far.
    int bytesleft = *N; // How many bytes we still need to send.
    int n; // How many we have sent in a transfer.

    while( sent < *N ) {

        
        n = send(comm_socket, pStart + sent, bytesleft, 0);
        //printf("-Sent %d bytes this loop. \n", n);

        if (n == -1) {
            perror("-Server: Failed to stream send.");
            printf("-Oh dear, something went wrong with recv()! %s \n", strerror(errno));
            exit(1); // Failed to send.
        }

        // Shift sent up by n and bytesleft down by n.
        sent += n;
        bytesleft -= n;
    }

    if ( sent != *N ) {
        perror("-Server: Warning didn't send all bytes.");
    }

    return sent; // return number actually sent here

}

void print_buffer(long *buffer, int words) {
    int i = 0;

    for (i=0; i<words; i++) {
        printf(" %ld", buffer[i]);
    }
    printf("\n");

}

void printword(unsigned long wd) {
    if ((wd&0xFFFF0000) == 0xFADC0000) 
	printf("\033[01;33m%08lx\033[0m ", wd);
    else if ((wd&0xFFFF0000) == 0xCAFE0000) 
	printf("\033[01;35m%08lx\033[0m ", wd);
    else 
	printf("%08lx ", wd);
}

void printBits(size_t const size, void const * const ptr) {
    unsigned char *b = (unsigned char*) ptr;
    unsigned char byte;
    int i, j;

    for (i=size-1;i>=0;i--)
    {
        for (j=7;j>=0;j--)
        {
            byte = (b[i] >> j) & 1;
            printf("%u", byte);
        }
    }
    puts("");
}
